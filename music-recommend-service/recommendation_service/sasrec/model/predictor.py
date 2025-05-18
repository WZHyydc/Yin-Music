import os

import torch
import numpy as np
import json
from typing import List, Dict
from config import MODEL_CONFIG, RECOMMEND_CONFIG
from sasrec.model.model import SASRec

class SASRecPredictor:
    def __init__(self):
        self.device = torch.device(
            'cuda' if torch.cuda.is_available() and os.getenv('USE_GPU', 'true').lower() == 'true' else 'cpu')
        self.model = self._load_model()
        self.model.eval()
        # 加载音频嵌入向量
        self.audio_embeddings = self._load_audio_embeddings()
        # 初始化模型的mean_audio_embedding
        self.model.load_audio_embeddings(MODEL_CONFIG['audio_embeddings_dir'])
        
    def _load_audio_embeddings(self) -> Dict[int, torch.Tensor]:
        """加载所有音频嵌入向量"""
        audio_embeddings = {}
        audio_embeddings_dir = MODEL_CONFIG['audio_embeddings_dir']
        
        for file_name in os.listdir(audio_embeddings_dir):
            if file_name.endswith('.npy'):
                song_id = int(file_name.split('.')[0])
                embedding_path = os.path.join(audio_embeddings_dir, file_name)
                embedding = np.load(embedding_path)
                audio_embeddings[song_id] = torch.tensor(embedding, dtype=torch.float32).to(self.device)
        
        return audio_embeddings
        
    def _load_model(self) -> torch.nn.Module:
        """加载预训练模型"""
        try:
            # 创建模型实例
            model = SASRec(
                num_items=MODEL_CONFIG['num_items'],
                audio_embedding_size=MODEL_CONFIG['audio_embedding_size'],
                hidden_size=MODEL_CONFIG['hidden_size'],
                num_heads=MODEL_CONFIG['num_heads'],
                num_layers=MODEL_CONFIG['num_layers'],
                dropout_rate=MODEL_CONFIG['dropout_rate'],
                max_seq_length=MODEL_CONFIG['sequence_length']
            )
            
            # 构建最佳模型路径
            model_path = os.path.join(MODEL_CONFIG['model_path'])
            
            # 加载checkpoint
            checkpoint = torch.load(model_path, map_location=self.device)
            # 从checkpoint中提取model_state_dict
            model.load_state_dict(checkpoint['model_state_dict'])
            model = model.to(self.device)
            return model
        except FileNotFoundError:
            raise Exception(f"最佳模型文件不存在: {model_path}，请先训练模型")
            
    def _prepare_input(self, user_features: Dict) -> torch.Tensor:
        """
        准备模型输入，整合用户的所有特征
        
        Args:
            user_features: 包含用户特征的字典，包括：
                - recent_plays: 最近播放的歌曲序列
                - favorite_songs: 收藏的歌曲列表
                - song_ratings: 歌曲评分字典
        """
        # 获取播放序列和收藏序列
        play_sequence = user_features['recent_plays']
        favorites = user_features['favorite_songs']
        ratings = user_features['song_ratings']
        
        # 计算收藏序列的最大长度（播放序列长度的0.6倍）
        favorite_max_length = int(MODEL_CONFIG['sequence_length'] * 0.6)
        
        # 处理收藏序列
        if len(favorites) > favorite_max_length:
            favorites = favorites[-favorite_max_length:]  # 保留最新的收藏
        
        # 计算播放序列的长度（总长度减去收藏序列长度）
        # 不可以使用最大序列长度 * 播放历史序列比例，因为有可能出现整数截断的问题而导致收藏序列长度
        # +播放序列长度不足最大序列长度
        play_sequence_length = MODEL_CONFIG['sequence_length'] - len(favorites)
        
        # 处理播放序列
        if len(play_sequence) > play_sequence_length:
            play_sequence = play_sequence[-play_sequence_length:]  # 保留最新的播放记录
        
        # 合并序列：收藏 + 播放
        combined_sequence = favorites + play_sequence
        
        # 如果总长度不足，在前面填充0
        if len(combined_sequence) < MODEL_CONFIG['sequence_length']:
            combined_sequence = [0] * (MODEL_CONFIG['sequence_length'] - len(combined_sequence)) + combined_sequence
        
        # 转换为tensor
        sequence_tensor = torch.tensor(combined_sequence, dtype=torch.long).unsqueeze(0).to(self.device)
        
        # 只保留序列中出现的歌曲的评分
        filtered_ratings = {
            song_id: float(rating) 
            for song_id, rating in ratings.items() 
            if song_id in combined_sequence
        }
        
        return sequence_tensor, filtered_ratings
        
    def predict_next(self, user_features: Dict) -> List[int]:
        """
        预测用户下一个可能喜欢的物品
        
        Args:
            user_features: 用户特征字典
            
        Returns:
            top_k_items: 推荐的物品ID列表
        """
        with torch.no_grad():
            # 准备输入
            sequence_tensor, filtered_ratings = self._prepare_input(user_features)
            
            # 创建评分tensor
            ratings_tensor = torch.zeros(sequence_tensor.shape, dtype=torch.float32, device=self.device)
            for idx, song_id in enumerate(sequence_tensor[0]):
                if song_id.item() in filtered_ratings:
                    ratings_tensor[0, idx] = filtered_ratings[song_id.item()]
            
            # 获取预测分数
            scores = self.model(sequence_tensor, ratings_tensor, self.audio_embeddings)
            
            # 将预测分数转换为numpy数组
            scores = scores.squeeze().cpu().numpy()
            
            # 根据评分调整分数
            for song_id, rating in filtered_ratings.items():
                if song_id < len(scores):
                    scores[song_id] *= (1 + float(rating))  # 使用乘法而不是加法来调整权重
            
            # 获取top-k推荐
            top_k_indices = np.argsort(scores)[-RECOMMEND_CONFIG['top_k']:][::-1]
            top_k_items = top_k_indices.tolist()
            
            return top_k_items
            
    def batch_predict(self, user_features_list: Dict[int, Dict]) -> Dict[int, List[int]]:
        """
        批量预测多个用户的推荐，使用 micro-batching 提升 GPU 利用率
        
        Args:
            user_features_list: 用户ID到特征字典的映射
            
        Returns:
            recommendations: 用户ID到推荐物品列表的映射
        """
        recommendations = {}
        batch_size = 512  # micro-batch 大小
        
        # 将用户特征列表转换为列表形式，保持顺序
        user_ids = list(user_features_list.keys())
        features_list = [user_features_list[uid] for uid in user_ids]
        
        # 按批次处理
        for i in range(0, len(user_ids), batch_size):
            batch_user_ids = user_ids[i:i + batch_size]
            batch_features = features_list[i:i + batch_size]
            
            # 准备批次输入
            batch_sequences = []
            batch_ratings = []
            
            for features in batch_features:
                sequence_tensor, filtered_ratings = self._prepare_input(features)
                batch_sequences.append(sequence_tensor)
                batch_ratings.append(filtered_ratings)
            
            # 将序列堆叠成批次
            batch_sequences = torch.cat(batch_sequences, dim=0)
            
            # 创建评分张量
            batch_ratings_tensor = torch.zeros(batch_sequences.shape, dtype=torch.float32, device=self.device)
            for idx, (sequence, ratings) in enumerate(zip(batch_sequences, batch_ratings)):
                for pos, song_id in enumerate(sequence):
                    if song_id.item() in ratings:
                        batch_ratings_tensor[idx, pos] = ratings[song_id.item()]
            
            # 批量预测
            with torch.no_grad():
                scores = self.model(batch_sequences, batch_ratings_tensor, self.audio_embeddings)
                
                # 处理每个用户的预测结果
                for j, user_id in enumerate(batch_user_ids):
                    user_scores = scores[j].cpu().numpy()
                    
                    # 根据评分调整分数
                    user_ratings = batch_ratings[j]
                    
                    # 获取top-k推荐
                    top_k_indices = np.argsort(user_scores)[-RECOMMEND_CONFIG['top_k']:][::-1]
                    recommendations[user_id] = top_k_indices.tolist()
        
        return recommendations