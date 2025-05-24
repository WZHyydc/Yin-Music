import os
import math
import logging
import copy

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Dict, List, Tuple, Optional

# 设置日志
logger = logging.getLogger(__name__)

class MultiHeadAttention(nn.Module):
    """多头注意力机制"""
    def __init__(self, hidden_size: int, num_heads: int, dropout_rate: float = 0.1):
        super().__init__()
        self.num_heads = num_heads
        self.hidden_size = hidden_size
        self.head_size = hidden_size // num_heads
        
        self.query = nn.Linear(hidden_size, hidden_size)
        self.key = nn.Linear(hidden_size, hidden_size)
        self.value = nn.Linear(hidden_size, hidden_size)
        self.dropout = nn.Dropout(dropout_rate)
        self.output = nn.Linear(hidden_size, hidden_size)
        
    def _rating_to_weight(self, rating: float) -> float:
        """
        将评分转换为注意力权重
        
        Args:
            rating: 用户评分 (0-10)
            
        Returns:
            注意力权重 (0-1)
        """
        if rating == 0:  # 没有评分
            return 1.0  # 保持原始注意力权重
        
        # 将评分归一化到[-1, 1]区间
        normalized_rating = (rating - 5) / 5.0  # 5分作为中间值
        
        # 使用sigmoid函数将评分映射到(0.5, 1.5)区间
        # 这样：低分(<5)会得到<1.0的权重，高分(>5)会得到>1.0的权重
        weight = 1.0 + torch.sigmoid(torch.tensor(normalized_rating * 2.0)).item()  # 2.0是斜率参数，可以调整
        
        return weight
        
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None, ratings: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        前向传播
        
        Args:
            x: 输入张量，形状为 [batch_size, seq_length, hidden_size]
            mask: 注意力掩码，形状为 [batch_size, seq_length, seq_length]
            ratings: 评分张量，形状为 [batch_size, seq_length]
        
        Returns:
            输出张量，形状为 [batch_size, seq_length, hidden_size]
        """
        batch_size, seq_length, hidden_size = x.shape
        
        # 线性变换
        q = self.query(x)  # [batch_size, seq_length, hidden_size]
        k = self.key(x)    # [batch_size, seq_length, hidden_size]
        v = self.value(x)  # [batch_size, seq_length, hidden_size]
        
        # 重塑为多头形式
        q = q.view(batch_size, seq_length, self.num_heads, self.head_size).transpose(1, 2)
        k = k.view(batch_size, seq_length, self.num_heads, self.head_size).transpose(1, 2)
        v = v.view(batch_size, seq_length, self.num_heads, self.head_size).transpose(1, 2)
        
        # 计算注意力分数
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_size)
        
        # 应用评分权重
        if ratings is not None:
            # 将评分转换为权重
            rating_weights = torch.tensor([[self._rating_to_weight(r.item()) for r in row] for row in ratings], 
                                        device=scores.device)
            # 扩展维度以匹配注意力分数
            rating_weights = rating_weights.unsqueeze(1).unsqueeze(2)  # [batch_size, 1, 1, seq_length]
            # 应用评分权重
            scores = scores * rating_weights
        
        # 应用掩码
        if mask is not None:
            # 扩展掩码以匹配多头注意力
            mask = mask.unsqueeze(1)  # [batch_size, 1, seq_length, seq_length]
            scores = scores.masked_fill(mask == 0, float('-inf'))
        
        # 应用softmax
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        # 计算输出
        output = torch.matmul(attention_weights, v)
        output = output.transpose(1, 2).contiguous().view(batch_size, seq_length, hidden_size)
        
        # 线性变换
        output = self.output(output)
        
        return output

class FeedForward(nn.Module):
    """前馈神经网络"""
    def __init__(self, hidden_size: int, dropout_rate: float = 0.1):
        super().__init__()
        self.linear1 = nn.Linear(hidden_size, hidden_size * 4)
        self.linear2 = nn.Linear(hidden_size * 4, hidden_size)
        self.dropout = nn.Dropout(dropout_rate)
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = F.relu(self.linear1(x))
        x = self.dropout(x)
        return self.linear2(x)

class TransformerBlock(nn.Module):
    """Transformer 块"""
    def __init__(self, hidden_size: int, num_heads: int, dropout_rate: float = 0.1):
        super().__init__()
        self.attention = MultiHeadAttention(hidden_size, num_heads, dropout_rate)
        self.feed_forward = FeedForward(hidden_size, dropout_rate)
        self.norm1 = nn.LayerNorm(hidden_size)
        self.norm2 = nn.LayerNorm(hidden_size)
        self.dropout = nn.Dropout(dropout_rate)
        
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None, ratings: Optional[torch.Tensor] = None) -> torch.Tensor:
        # 自注意力层
        attention_output = self.attention(self.norm1(x), mask, ratings)
        x = x + self.dropout(attention_output)
        
        # 前馈网络
        feed_forward_output = self.feed_forward(self.norm2(x))
        x = x + self.dropout(feed_forward_output)
        
        return x

class SASRec(nn.Module):
    """改进的SASRec模型，支持音频特征和评分加权"""
    def __init__(
        self,
        num_items: int,
        audio_embedding_size: int = 512,
        hidden_size: int = 64,
        num_heads: int = 4,
        num_layers: int = 2,
        dropout_rate: float = 0.1,
        max_seq_length: int = 50
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.max_seq_length = max_seq_length
        self.audio_embedding_size = audio_embedding_size
        
        # 物品ID嵌入层
        self.item_embedding = nn.Embedding(num_items + 1, hidden_size, padding_idx=0)
        
        # 音频特征投影层
        self.audio_projection = nn.Linear(audio_embedding_size, hidden_size)
        
        # 位置编码
        self.position_embedding = nn.Embedding(max_seq_length, hidden_size)
        
        # Transformer层
        self.transformer_layers = nn.ModuleList([
            TransformerBlock(hidden_size, num_heads, dropout_rate)
            for _ in range(num_layers)
        ])
        
        self.dropout = nn.Dropout(dropout_rate)
        self.layer_norm = nn.LayerNorm(hidden_size)
        
        # 输出层
        self.output_layer = nn.Linear(hidden_size, num_items + 1)
        
        # 在初始化时计算所有嵌入向量的平均值
        self.mean_audio_embedding = None
        
    def load_audio_embeddings(self, audio_embeddings_dir: str):
        """加载音频嵌入向量"""
        self.audio_embeddings = {}
        all_embeddings = []
        
        # 首先检查所有嵌入向量的维度
        for file_name in os.listdir(audio_embeddings_dir):
            if file_name.endswith('.npy'):
                embedding = np.load(os.path.join(audio_embeddings_dir, file_name))
                logger.info(f"加载文件 {file_name} 的嵌入向量，原始维度: {embedding.shape}")
                if len(embedding.shape) > 1:
                    # 如果是多维的，取第一个维度
                    embedding = embedding[0]
                    logger.info(f"多维嵌入向量，取第一个维度后的形状: {embedding.shape}")
                all_embeddings.append(embedding)
        
        if not all_embeddings:
            raise ValueError("没有找到任何音频嵌入向量文件")
            
        # 确保所有嵌入向量都是正确的维度
        for file_name in os.listdir(audio_embeddings_dir):
            if file_name.endswith('.npy'):
                song_id = int(file_name.split('.')[0])
                embedding = np.load(os.path.join(audio_embeddings_dir, file_name))
                logger.info(f"处理文件 {file_name} 的嵌入向量，原始维度: {embedding.shape}")
                
                # 处理多维嵌入向量
                if len(embedding.shape) > 1:
                    embedding = embedding[0]
                    logger.info(f"多维嵌入向量，取第一个维度后的形状: {embedding.shape}")
                
                # 确保维度正确
                if embedding.shape[0] != self.audio_embedding_size:
                    logger.warning(f"嵌入向量维度不匹配: {embedding.shape[0]} != {self.audio_embedding_size}")
                    if embedding.shape[0] > self.audio_embedding_size:
                        # 如果维度太大，进行截断
                        embedding = embedding[:self.audio_embedding_size]
                        logger.info(f"截断后的维度: {embedding.shape}")
                    else:
                        # 如果维度太小，进行零填充
                        padding = np.zeros(self.audio_embedding_size - embedding.shape[0])
                        embedding = np.concatenate([embedding, padding])
                        logger.info(f"填充后的维度: {embedding.shape}")
                
                self.audio_embeddings[song_id] = torch.tensor(embedding, dtype=torch.float32)
                logger.info(f"最终存储的嵌入向量维度: {self.audio_embeddings[song_id].shape}")
        
        # 计算平均嵌入向量
        self.mean_audio_embedding = torch.tensor(
            np.mean(all_embeddings, axis=0),
            dtype=torch.float32
        )
        logger.info(f"平均嵌入向量维度: {self.mean_audio_embedding.shape}")
        
        logger.info(f"成功加载 {len(self.audio_embeddings)} 个音频嵌入向量，维度为 {self.audio_embedding_size}")
        
    def forward(
        self,
        input_ids: torch.Tensor,
        ratings: torch.Tensor,
        audio_embeddings: Dict[int, torch.Tensor]
    ) -> torch.Tensor:
        """
        前向传播
        
        Args:
            input_ids: 输入序列，形状为 [batch_size, seq_length]
            ratings: 评分序列，形状为 [batch_size, seq_length]
            audio_embeddings: 音频嵌入向量字典
        
        Returns:
            预测分数，形状为 [batch_size, num_items]
        """
        batch_size, seq_length = input_ids.shape
        
        # 获取物品嵌入
        item_embeddings = self.item_embedding(input_ids)  # [batch_size, seq_length, hidden_size]
        
        # 获取位置编码
        position_ids = torch.arange(seq_length, device=input_ids.device).unsqueeze(0)
        position_embeddings = self.position_embedding(position_ids)  # [1, seq_length, hidden_size]
        
        # 获取音频特征
        audio_features = []
        for i in range(batch_size):
            seq_audio_features = []
            for j in range(seq_length):
                song_id = input_ids[i, j].item()
                if song_id in audio_embeddings:
                    audio_feat = audio_embeddings[song_id]
                    # 确保音频特征维度正确
                    if len(audio_feat.shape) > 1:
                        # 如果是2维的，取第一个维度
                        audio_feat = audio_feat[0]
                    
                    if audio_feat.shape[0] != self.audio_embedding_size:
                        logger.warning(f"Audio feature dimension mismatch for song {song_id}: expected {self.audio_embedding_size}, got {audio_feat.shape[0]}")
                        if audio_feat.shape[0] > self.audio_embedding_size:
                            audio_feat = audio_feat[:self.audio_embedding_size]
                        else:
                            # 确保padding和audio_feat具有相同的维度
                            padding = torch.zeros(self.audio_embedding_size - audio_feat.shape[0], device=audio_feat.device)
                            audio_feat = torch.cat([audio_feat, padding], dim=0)
                else:
                    # 使用全局平均嵌入向量作为默认值
                    audio_feat = self.mean_audio_embedding.to(input_ids.device)
                seq_audio_features.append(audio_feat)
            # 堆叠序列中的音频特征
            seq_audio_features = torch.stack(seq_audio_features)  # [seq_length, audio_embedding_size]
            audio_features.append(seq_audio_features)
        # 堆叠批次中的音频特征
        audio_features = torch.stack(audio_features)  # [batch_size, seq_length, audio_embedding_size]
        
        # 将音频特征投影到 hidden_size 维度
        audio_features = self.audio_projection(audio_features)  # [batch_size, seq_length, hidden_size]
        
        # 合并嵌入
        embeddings = item_embeddings + position_embeddings + audio_features
        # 创建注意力掩码
        attention_mask = (input_ids != 0).unsqueeze(1).unsqueeze(2)  # [batch_size, 1, 1, seq_length]
        attention_mask = attention_mask.squeeze(1)  # [batch_size, 1, seq_length]
        attention_mask = attention_mask.expand(batch_size, seq_length, seq_length)  # [batch_size, seq_length, seq_length]
        
        # 应用Transformer编码器
        hidden_states = embeddings
        for layer in self.transformer_layers:
            hidden_states = layer(hidden_states, attention_mask, ratings)
        
        # 获取序列表示
        sequence_representation = hidden_states[:, -1]  # [batch_size, hidden_size]
        
        # 计算预测分数
        scores = self.output_layer(sequence_representation)  # [batch_size, num_items]
        
        return scores

def ablation_study(model, val_loader, device):
    # 完整模型
    full_metrics = evaluate_model(model, val_loader, device)
    
    # 移除音频特征
    model_no_audio = copy.deepcopy(model)
    model_no_audio.audio_projection.weight.data.zero_()
    no_audio_metrics = evaluate_model(model_no_audio, val_loader, device)
    
    # 移除位置编码
    model_no_pos = copy.deepcopy(model)
    model_no_pos.position_embedding.weight.data.zero_()
    no_pos_metrics = evaluate_model(model_no_pos, val_loader, device)
    
    return {
        'full_model': full_metrics,
        'no_audio': no_audio_metrics,
        'no_position': no_pos_metrics
    }