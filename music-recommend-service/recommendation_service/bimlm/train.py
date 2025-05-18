import os
import json
import logging
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np
from tqdm import tqdm
from pathlib import Path
import time
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.metrics import ndcg_score, precision_score, recall_score

from bimlm.model.model import BiMLM
from config import MODEL_CONFIG, RECOMMEND_CONFIG, MODEL_OUTPUT_DIR

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 模型名称常量
MODEL_NAME = "bimlm"

def data_augmentation(data: pd.DataFrame) -> pd.DataFrame:
    """
    对用户数据进行增强处理
    
    Args:
        data: 原始用户数据DataFrame
        
    Returns:
        增强后的用户数据DataFrame
    """
    # 获取配置参数
    sequence_length = MODEL_CONFIG['sequence_length']
    favorite_ratio = MODEL_CONFIG['favorite_ratio']
    favorite_length = int(sequence_length * favorite_ratio)
    playhistory_length = sequence_length - favorite_length
    
    # 存储增强后的数据
    augmented_data = []
    new_user_id = 0  # 新的用户ID计数器
    
    # 对每个用户进行处理
    for _, row in tqdm(data.iterrows(), total=len(data), desc="数据增强"):
        # 解析用户数据
        recent_plays = json.loads(row['recent_plays'])
        favorite_songs = json.loads(row['favorite_songs'])
        song_ratings = json.loads(row['song_ratings'])
        
        # 如果收藏歌曲数量不足，用0填充在前面
        if len(favorite_songs) < favorite_length:
            favorite_songs = [0] * (favorite_length - len(favorite_songs)) + favorite_songs
        
        # 对收藏歌曲使用滑动窗口
        favorite_windows = []
        for i in range(len(favorite_songs) - favorite_length + 1):
            favorite_windows.append(favorite_songs[i:i + favorite_length])
        
        # 对播放历史使用滑动窗口
        playhistory_windows = []
        for i in range(len(recent_plays) - playhistory_length + 1):
            playhistory_windows.append(recent_plays[i:i + playhistory_length])
        
        # 如果收藏歌曲或播放历史长度不足，至少保留一个窗口
        if not favorite_windows:
            favorite_windows = [favorite_songs[:favorite_length]]
        if not playhistory_windows:
            playhistory_windows = [recent_plays[:playhistory_length]]
        
        # 组合所有可能的窗口对
        for play_window in playhistory_windows:
            for fav_window in favorite_windows:
                # 构建完整序列（播放历史 + 收藏歌曲）
                sequence = play_window + fav_window
                
                # 构建评分序列
                ratings = [song_ratings.get(str(song_id), 0) for song_id in sequence]
                
                # 创建新的数据行
                new_row = {
                    'user_id': new_user_id,
                    'recent_plays': json.dumps(play_window),
                    'favorite_songs': json.dumps(fav_window),
                    'song_ratings': json.dumps({str(song_id): rating for song_id, rating in zip(sequence, ratings)})
                }
                
                augmented_data.append(new_row)
                new_user_id += 1
    
    # 转换为DataFrame
    augmented_df = pd.DataFrame(augmented_data)

    logger.info(f"Data augmentation completed: original data {len(data)} rows, augmented data {len(augmented_df)} rows")
    logger.info(f"Average {len(augmented_df)/len(data):.2f} augmented data per original user")
    
    return augmented_df

class MusicDataset(Dataset):
    """音乐数据集"""
    def __init__(self, data: pd.DataFrame, max_seq_length: int, audio_embeddings_dir: str):
        """
        初始化数据集
        
        Args:
            data: 包含用户序列的DataFrame
            max_seq_length: 最大序列长度
            audio_embeddings_dir: 音频嵌入向量目录
        """
        self.data = data
        self.max_seq_length = max_seq_length
        self.audio_embeddings_dir = audio_embeddings_dir
        
    def __len__(self) -> int:
        return len(self.data)
        
    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        # 获取用户数据
        user_data = self.data.iloc[idx]
        
        # 解析最近播放序列
        recent_plays = json.loads(user_data['recent_plays'])
        
        # 解析收藏歌曲
        favorite_songs = json.loads(user_data['favorite_songs'])
        
        # 解析评分
        song_ratings = json.loads(user_data['song_ratings'])
        
        # 构建完整序列（收藏歌曲 + 最近播放）
        sequence = favorite_songs + recent_plays
        
        # 构建评分序列
        ratings = [song_ratings.get(str(song_id), 0) for song_id in sequence]
        
        # 如果序列长度超过最大长度，则截断
        if len(sequence) > self.max_seq_length:
            sequence = sequence[-self.max_seq_length:]
            ratings = ratings[-self.max_seq_length:]
            
        # 填充序列
        input_ids = torch.zeros(self.max_seq_length, dtype=torch.long)
        input_ids[-len(sequence):] = torch.tensor(sequence)
        
        # 填充评分
        input_ratings = torch.zeros(self.max_seq_length, dtype=torch.float)
        input_ratings[-len(ratings):] = torch.tensor(ratings)
        
        return input_ids, input_ratings

def calculate_metrics(scores: torch.Tensor, targets: torch.Tensor) -> Dict[str, float]:
    """
    计算评估指标
    
    Args:
        scores: 预测分数 [batch_size, num_items]
        targets: 目标物品 [batch_size]
        
    Returns:
        评估指标字典
    """
    # 获取top-k推荐
    _, top_k_indices = torch.topk(scores, k=10, dim=1)
    
    # 转换为numpy数组
    top_k_indices = top_k_indices.cpu().detach().numpy()
    targets = targets.cpu().detach().numpy()
    scores_np = scores.cpu().detach().numpy()
    
    # 处理无穷大和NaN值
    scores_np = np.nan_to_num(scores_np, nan=-1e9, posinf=1e9, neginf=-1e9)
    
    # 计算NDCG@10
    ndcg = ndcg_score(
        [[1 if i == t else 0 for i in range(scores.size(1))] for t in targets],
        scores_np,
        k=10
    )
    
    # 计算Precision@10
    y_true = np.zeros((len(targets), scores.size(1)))
    for i, t in enumerate(targets):
        y_true[i, t] = 1
    
    y_pred = np.zeros((len(targets), scores.size(1)))
    for i, indices in enumerate(top_k_indices):
        y_pred[i, indices] = 1
    
    precision = precision_score(y_true, y_pred, average='micro')
    
    # 计算Recall@10
    recall = recall_score(y_true, y_pred, average='micro')
    
    return {
        'ndcg@10': ndcg,
        'precision@10': precision,
        'recall@10': recall
    }

def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
    num_epochs: int,
    checkpoint_dir: str = None,
    patience: int = 5
) -> Tuple[nn.Module, Dict[str, List[float]]]:
    """
    训练模型
    
    Args:
        model: 模型
        train_loader: 训练数据加载器
        val_loader: 验证数据加载器
        criterion: 损失函数
        optimizer: 优化器
        device: 设备
        num_epochs: 训练轮数
        checkpoint_dir: 检查点保存目录
        patience: 早停耐心值
    
    Returns:
        训练好的模型，指标历史记录
    """
    # 创建检查点目录
    if checkpoint_dir is None:
        checkpoint_dir = MODEL_CONFIG['checkpoint_dir']
    checkpoint_dir = Path(checkpoint_dir)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化学习率调度器
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        factor=0.5,
        patience=3,
        verbose=True,
        min_lr=1e-6
    )
    
    # 初始化训练记录
    best_val_loss = float('inf')
    metrics_history = {
        'train_loss': [],
        'val_loss': [],
        'train_ndcg@10': [],
        'val_ndcg@10': [],
        'train_precision@10': [],
        'val_precision@10': [],
        'train_recall@10': [],
        'val_recall@10': []
    }
    no_improve = 0
    start_time = time.time()
    
    # 训练循环
    for epoch in range(num_epochs):
        # 训练阶段
        model.train()
        train_loss = 0
        train_steps = 0
        train_metrics = {
            'ndcg@10': 0,
            'precision@10': 0,
            'recall@10': 0
        }
        
        train_pbar = tqdm(
            train_loader,
            desc=f"Epoch {epoch + 1}/{num_epochs} [Train]",
            leave=True
        )
        
        for sequences, ratings in train_pbar:
            sequences = sequences.to(device)
            ratings = ratings.to(device)
            
            optimizer.zero_grad()
            
            # 前向传播（训练模式）
            scores, mask_loss = model(sequences, ratings, model.audio_embeddings, training=True)
            
            # 检查分数是否包含NaN
            if torch.isnan(scores).any():
                print(f"Warning: NaN detected in scores at step {train_steps}")
                print(f"Score stats: min={scores.min().item()}, max={scores.max().item()}, mean={scores.mean().item()}")
                continue
            
            # 计算损失
            next_item_loss = criterion(scores[:, -1], sequences[:, -1])
            loss = next_item_loss + mask_loss if mask_loss is not None else next_item_loss
            
            # 检查损失是否为NaN
            if torch.isnan(loss):
                print(f"Warning: NaN detected in loss at step {train_steps}")
                print(f"Score stats: min={scores.min().item()}, max={scores.max().item()}, mean={scores.mean().item()}")
                continue
            
            # 反向传播
            loss.backward()
            
            # 检查梯度
            grad_norm = 0
            for param in model.parameters():
                if param.grad is not None:
                    grad_norm += param.grad.norm().item() ** 2
            grad_norm = grad_norm ** 0.5
            
            if grad_norm > 10:
                print(f"Warning: Large gradient norm detected: {grad_norm}")
                torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            
            optimizer.step()
            
            # 计算指标
            metrics = calculate_metrics(scores[:, -1], sequences[:, -1])
            for k, v in metrics.items():
                train_metrics[k] += v
            
            # 更新统计信息
            train_loss += loss.item()
            train_steps += 1
            
            # 更新进度条
            train_pbar.set_postfix({
                'loss': f'{loss.item():.4f}',
                'avg_loss': f'{train_loss/train_steps:.4f}',
                'ndcg@10': f'{train_metrics["ndcg@10"]/train_steps:.4f}',
                'grad_norm': f'{grad_norm:.4f}'
            })
        
        # 计算平均训练指标
        avg_train_loss = train_loss / len(train_loader)
        for k in train_metrics:
            train_metrics[k] /= len(train_loader)
        
        # 验证阶段
        model.eval()
        val_loss = 0
        val_steps = 0
        val_metrics = {
            'ndcg@10': 0,
            'precision@10': 0,
            'recall@10': 0
        }
        
        with torch.no_grad():
            val_pbar = tqdm(
                val_loader,
                desc=f"Epoch {epoch + 1}/{num_epochs} [Val]",
                leave=True
            )
            
            for sequences, ratings in val_pbar:
                sequences = sequences.to(device)
                ratings = ratings.to(device)
                
                # 前向传播（评估模式）
                scores, _ = model(sequences, ratings, model.audio_embeddings, training=False)
                loss = criterion(scores[:, -1], sequences[:, -1])
                
                # 计算指标
                metrics = calculate_metrics(scores[:, -1], sequences[:, -1])
                for k, v in metrics.items():
                    val_metrics[k] += v
                
                val_loss += loss.item()
                val_steps += 1
                
                val_pbar.set_postfix({
                    'loss': f'{loss.item():.4f}',
                    'avg_loss': f'{val_loss/val_steps:.4f}',
                    'ndcg@10': f'{val_metrics["ndcg@10"]/val_steps:.4f}'
                })
        
        # 计算平均验证指标
        avg_val_loss = val_loss / len(val_loader)
        for k in val_metrics:
            val_metrics[k] /= len(val_loader)
        
        # 更新学习率
        scheduler.step(avg_val_loss)
        
        # 记录指标
        metrics_history['train_loss'].append(avg_train_loss)
        metrics_history['val_loss'].append(avg_val_loss)
        metrics_history['train_ndcg@10'].append(train_metrics['ndcg@10'])
        metrics_history['val_ndcg@10'].append(val_metrics['ndcg@10'])
        metrics_history['train_precision@10'].append(train_metrics['precision@10'])
        metrics_history['val_precision@10'].append(val_metrics['precision@10'])
        metrics_history['train_recall@10'].append(train_metrics['recall@10'])
        metrics_history['val_recall@10'].append(val_metrics['recall@10'])
        
        # 记录训练信息
        elapsed_time = time.time() - start_time
        logger.info(
            f"Epoch {epoch + 1}/{num_epochs} - "
            f"Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}, "
            f"Train NDCG@10: {train_metrics['ndcg@10']:.4f}, "
            f"Val NDCG@10: {val_metrics['ndcg@10']:.4f}, "
            f"Time: {elapsed_time:.2f}s"
        )
        
        # 保存最佳模型
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            no_improve = 0
            
            # 保存检查点
            checkpoint = {
                'epoch': epoch + 1,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': avg_val_loss,
                'metrics_history': metrics_history
            }
            torch.save(
                checkpoint,
                checkpoint_dir / f"{MODEL_NAME}_epoch_{epoch + 1}.pth"
            )
            
            # 保存最佳模型
            torch.save(
                checkpoint,
                checkpoint_dir / f"{MODEL_NAME}_best.pth"
            )
        else:
            no_improve += 1
            
        # 早停
        if no_improve >= patience:
            logger.info(f"Early stopping at epoch {epoch + 1}")
            break
    
    return model, metrics_history

def plot_training_metrics(metrics_history: Dict[str, List[float]], output_dir: str):
    """
    Plot training metrics
    
    Args:
        metrics_history: Training metrics history
        output_dir: Output directory
    """
    # Create output directory
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Training Metrics', fontsize=16)
    
    # Plot loss curves
    axes[0, 0].plot(metrics_history['train_loss'], label='Train Loss')
    axes[0, 0].plot(metrics_history['val_loss'], label='Val Loss')
    axes[0, 0].set_title('Loss Curves')
    axes[0, 0].set_xlabel('Epoch')
    axes[0, 0].set_ylabel('Loss')
    axes[0, 0].legend()
    axes[0, 0].grid(True)
    
    # Plot NDCG@10 curves
    axes[0, 1].plot(metrics_history['train_ndcg@10'], label='Train NDCG@10')
    axes[0, 1].plot(metrics_history['val_ndcg@10'], label='Val NDCG@10')
    axes[0, 1].set_title('NDCG@10 Curves')
    axes[0, 1].set_xlabel('Epoch')
    axes[0, 1].set_ylabel('NDCG@10')
    axes[0, 1].legend()
    axes[0, 1].grid(True)
    
    # Plot Precision@10 curves
    axes[1, 0].plot(metrics_history['train_precision@10'], label='Train Precision@10')
    axes[1, 0].plot(metrics_history['val_precision@10'], label='Val Precision@10')
    axes[1, 0].set_title('Precision@10 Curves')
    axes[1, 0].set_xlabel('Epoch')
    axes[1, 0].set_ylabel('Precision@10')
    axes[1, 0].legend()
    axes[1, 0].grid(True)
    
    # Plot Recall@10 curves
    axes[1, 1].plot(metrics_history['train_recall@10'], label='Train Recall@10')
    axes[1, 1].plot(metrics_history['val_recall@10'], label='Val Recall@10')
    axes[1, 1].set_title('Recall@10 Curves')
    axes[1, 1].set_xlabel('Epoch')
    axes[1, 1].set_ylabel('Recall@10')
    axes[1, 1].legend()
    axes[1, 1].grid(True)
    
    # Adjust layout
    plt.tight_layout()
    
    # Save figure
    plt.savefig(output_dir / f"{MODEL_NAME}_training_metrics.png", dpi=300, bbox_inches='tight')
    plt.close()
    
    # Save detailed metrics data
    metrics_data = {
        'epochs': list(range(1, len(metrics_history['train_loss']) + 1)),
        'train_loss': metrics_history['train_loss'],
        'val_loss': metrics_history['val_loss'],
        'train_ndcg@10': metrics_history['train_ndcg@10'],
        'val_ndcg@10': metrics_history['val_ndcg@10'],
        'train_precision@10': metrics_history['train_precision@10'],
        'val_precision@10': metrics_history['val_precision@10'],
        'train_recall@10': metrics_history['train_recall@10'],
        'val_recall@10': metrics_history['val_recall@10']
    }
    
    with open(output_dir / f"{MODEL_NAME}_metrics_data.json", 'w') as f:
        json.dump(metrics_data, f, indent=4)

def main():
    # 设置设备
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    # 加载数据
    data_path = os.path.join(MODEL_CONFIG['user_data_path'])
    logger.info(f"Loading data from {data_path}")
    
    try:
        data = pd.read_csv(data_path)
        logger.info(f"Successfully loaded original_data with {len(data)} users")
    except Exception as e:
        logger.error(f"Error loading data: {str(e)}")
        raise
    
    # 数据增强
    data = data_augmentation(data)
    logger.info(f"Successfully augmented data with {len(data)} users")
    
    # 按8:2的比例划分训练集和验证集
    train_size = int(len(data) * 0.8)
    train_data = data[:train_size]
    val_data = data[train_size:]
    
    logger.info(f"训练集大小: {len(train_data)}, 验证集大小: {len(val_data)}")
    
    # 创建数据集
    train_dataset = MusicDataset(
        train_data,
        MODEL_CONFIG['max_seq_length'],
        MODEL_CONFIG['audio_embeddings_dir']
    )
    val_dataset = MusicDataset(
        val_data,
        MODEL_CONFIG['max_seq_length'],
        MODEL_CONFIG['audio_embeddings_dir']
    )
    
    # 创建数据加载器
    train_loader = DataLoader(
        train_dataset,
        batch_size=MODEL_CONFIG['batch_size'],
        shuffle=True,
        num_workers=4
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=MODEL_CONFIG['batch_size'],
        shuffle=False,
        num_workers=4
    )
    
    # 创建模型
    model = BiMLM(
        num_items=MODEL_CONFIG['num_items'],
        audio_embedding_size=MODEL_CONFIG['audio_embedding_size'],
        hidden_size=MODEL_CONFIG['hidden_size'],
        num_heads=MODEL_CONFIG['num_heads'],
        num_layers=MODEL_CONFIG['num_layers'],
        dropout_rate=MODEL_CONFIG['dropout_rate'],
        max_seq_length=MODEL_CONFIG['max_seq_length'],
        mask_prob=MODEL_CONFIG.get('mask_prob', 0.15)
    ).to(device)
    
    # 加载音频嵌入向量
    model.load_audio_embeddings(MODEL_CONFIG['audio_embeddings_dir'])
    
    # 定义损失函数和优化器
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    
    # 使用AdamW优化器
    optimizer = optim.AdamW(
        model.parameters(),
        lr=1e-4,  # 降低学习率
        weight_decay=0.01,
        betas=(0.9, 0.999),
        eps=1e-8
    )
    
    # 训练模型
    model, metrics_history = train_model(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        criterion=criterion,
        optimizer=optimizer,
        device=device,
        num_epochs=MODEL_CONFIG['num_epochs'],
        checkpoint_dir=MODEL_CONFIG['checkpoint_dir'],
        patience=MODEL_CONFIG['early_stopping_patience']
    )
    
    # 保存训练历史
    history = {
        'train_losses': metrics_history['train_loss'],
        'val_losses': metrics_history['val_loss']
    }
    history_path = os.path.join(MODEL_OUTPUT_DIR, f"{MODEL_NAME}_history.json")
    with open(history_path, 'w') as f:
        json.dump(history, f)
    
    # 绘制训练指标变化趋势图
    plot_training_metrics(metrics_history, MODEL_OUTPUT_DIR)
    logger.info(f"训练指标图表已保存到 {MODEL_OUTPUT_DIR}")

if __name__ == "__main__":
    main() 