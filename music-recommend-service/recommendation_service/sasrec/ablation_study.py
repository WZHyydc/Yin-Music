import os
import json
import logging
import copy
import torch
import torch.nn as nn
import numpy as np
from typing import Dict, List, Tuple
from tqdm import tqdm
import matplotlib.pyplot as plt
from sklearn.metrics import ndcg_score, precision_score, recall_score

from sasrec.model.model import SASRec
from sasrec.train import calculate_metrics, custom_collate_fn
from config import MODEL_CONFIG, MODEL_OUTPUT_DIR

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 模型名称常量
MODEL_NAME = "sasrec"

def evaluate_model(model: nn.Module, val_loader: torch.utils.data.DataLoader, device: torch.device) -> Dict[str, float]:
    """
    评估模型性能
    
    Args:
        model: 模型
        val_loader: 验证数据加载器
        device: 设备
    
    Returns:
        评估指标字典
    """
    model.eval()
    val_metrics = {
        'ndcg@10': 0,
        'precision@10': 0,
        'recall@10': 0
    }
    
    with torch.no_grad():
        for sequences, ratings, audio_embeddings in tqdm(val_loader, desc="Evaluating"):
            sequences = sequences.to(device)
            ratings = ratings.to(device)
            
            scores = model(sequences, ratings, audio_embeddings)
            metrics = calculate_metrics(scores, sequences[:, -1])
            
            for k, v in metrics.items():
                val_metrics[k] += v
    
    # 计算平均值
    for k in val_metrics:
        val_metrics[k] /= len(val_loader)
    
    return val_metrics

def create_ablation_models(model: nn.Module) -> Dict[str, nn.Module]:
    """
    创建消融实验模型
    
    Args:
        model: 原始模型
    
    Returns:
        消融实验模型字典
    """
    ablation_models = {}
    
    # 1. 移除音频特征
    model_no_audio = copy.deepcopy(model)
    model_no_audio.audio_projection.weight.data.zero_()
    model_no_audio.audio_projection.bias.data.zero_()
    ablation_models['no_audio'] = model_no_audio
    
    # 2. 移除位置编码
    model_no_pos = copy.deepcopy(model)
    model_no_pos.position_embedding.weight.data.zero_()
    ablation_models['no_position'] = model_no_pos
    
    # 3. 移除评分加权
    model_no_rating = copy.deepcopy(model)
    for layer in model_no_rating.transformer_layers:
        layer.attention._rating_to_weight = lambda x: 1.0
    ablation_models['no_rating'] = model_no_rating
    
    # 4. 移除多头注意力（使用单头）
    model_single_head = copy.deepcopy(model)
    for layer in model_single_head.transformer_layers:
        layer.attention.num_heads = 1
        layer.attention.head_size = layer.attention.hidden_size
    ablation_models['single_head'] = model_single_head
    
    return ablation_models

def run_ablation_study(
    model: nn.Module,
    val_loader: torch.utils.data.DataLoader,
    device: torch.device,
    save_dir: str = None
) -> Dict[str, Dict[str, float]]:
    """
    运行消融实验
    
    Args:
        model: 原始模型
        val_loader: 验证数据加载器
        device: 设备
        save_dir: 结果保存目录
    
    Returns:
        消融实验结果字典
    """
    if save_dir is None:
        save_dir = os.path.join(MODEL_OUTPUT_DIR, f'{MODEL_NAME}_ablation_study')
    os.makedirs(save_dir, exist_ok=True)
    
    # 创建消融实验模型
    ablation_models = create_ablation_models(model)
    
    # 评估原始模型
    logger.info("Evaluating full model...")
    full_metrics = evaluate_model(model, val_loader, device)
    
    # 评估消融实验模型
    ablation_results = {'full_model': full_metrics}
    for name, ablation_model in ablation_models.items():
        logger.info(f"Evaluating {name} model...")
        ablation_model = ablation_model.to(device)
        metrics = evaluate_model(ablation_model, val_loader, device)
        ablation_results[name] = metrics
    
    # 保存结果
    results_path = os.path.join(save_dir, f'{MODEL_NAME}_ablation_results.json')
    with open(results_path, 'w') as f:
        json.dump(ablation_results, f, indent=4)
    
    # 绘制结果对比图
    plot_ablation_results(ablation_results, save_dir)
    
    return ablation_results

def plot_ablation_results(results: Dict[str, Dict[str, float]], save_dir: str):
    """
    绘制消融实验结果对比图
    
    Args:
        results: 消融实验结果
        save_dir: 保存目录
    """
    metrics = ['ndcg@10', 'precision@10', 'recall@10']
    models = list(results.keys())
    
    plt.figure(figsize=(15, 5))
    
    for i, metric in enumerate(metrics, 1):
        plt.subplot(1, 3, i)
        values = [results[model][metric] for model in models]
        plt.bar(models, values)
        plt.title(f'{metric} Comparison')
        plt.xticks(rotation=45)
        plt.ylabel(metric)
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, f'{MODEL_NAME}_ablation_results.png'))
    plt.close()

def main():
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    # 加载最佳模型
    model_path = os.path.join(MODEL_CONFIG['checkpoint_dir'], f'{MODEL_NAME}_best.pth')
    checkpoint = torch.load(model_path, map_location=device)
    
    # 创建模型
    model = SASRec(
        num_items=MODEL_CONFIG['num_items'],
        audio_embedding_size=MODEL_CONFIG['audio_embedding_size'],
        hidden_size=MODEL_CONFIG['hidden_size'],
        num_heads=MODEL_CONFIG['num_heads'],
        num_layers=MODEL_CONFIG['num_layers'],
        dropout_rate=MODEL_CONFIG['dropout_rate'],
        max_seq_length=MODEL_CONFIG['max_seq_length']
    ).to(device)
    
    # 加载模型权重
    model.load_state_dict(checkpoint['model_state_dict'])
    
    # 加载音频嵌入向量
    logger.info("Loading audio embeddings...")
    model.load_audio_embeddings(MODEL_CONFIG['audio_embeddings_dir'])
    logger.info("Audio embeddings loaded successfully")
    
    # 加载验证数据
    from sasrec.train import MusicDataset, DataLoader
    import pandas as pd
    
    # 首先读取完整数据
    full_data = pd.read_csv(MODEL_CONFIG['user_data_path'])
    logger.info(f"Loaded full dataset with {len(full_data)} rows")
    
    # 然后进行训练集和验证集的划分
    train_size = int(len(full_data) * 0.8)
    val_data = full_data[train_size:]
    logger.info(f"Validation set size: {len(val_data)} rows")
    
    val_dataset = MusicDataset(
        val_data,
        MODEL_CONFIG['max_seq_length'],
        MODEL_CONFIG['audio_embeddings_dir']
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=MODEL_CONFIG['batch_size'],
        shuffle=False,
        num_workers=4,
        collate_fn=custom_collate_fn
    )
    
    # 运行消融实验
    results = run_ablation_study(model, val_loader, device)
    
    # 打印结果
    logger.info("\nAblation Study Results:")
    for model_name, metrics in results.items():
        logger.info(f"\n{model_name}:")
        for metric_name, value in metrics.items():
            logger.info(f"{metric_name}: {value:.4f}")

if __name__ == "__main__":
    main() 