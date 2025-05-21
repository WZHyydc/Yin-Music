import os
import math
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional

# 设置日志
logger = logging.getLogger(__name__)

class PositionalEmbedding(nn.Module):
    """位置编码"""
    def __init__(self, max_seq_length: int, hidden_size: int):
        super().__init__()
        self.position_embedding = nn.Embedding(max_seq_length, hidden_size)
        self._init_weights()
        
    def _init_weights(self):
        nn.init.normal_(self.position_embedding.weight, mean=0.0, std=0.02)
        
    def forward(self, seq_length: int, device: torch.device) -> torch.Tensor:
        position_ids = torch.arange(seq_length, device=device).unsqueeze(0)
        return self.position_embedding(position_ids)

class ItemEmbedding(nn.Module):
    """物品编码"""
    def __init__(self, num_items: int, hidden_size: int):
        super().__init__()
        self.item_embedding = nn.Embedding(num_items + 2, hidden_size, padding_idx=0)  # +2 for mask token
        self._init_weights()
        
    def _init_weights(self):
        nn.init.normal_(self.item_embedding.weight, mean=0.0, std=0.02)
        
    def forward(self, input_ids: torch.Tensor) -> torch.Tensor:
        return self.item_embedding(input_ids)

class AudioEmbedding(nn.Module):
    """音频特征编码"""
    def __init__(self, audio_embedding_size: int, hidden_size: int, dropout_rate: float = 0.1):
        super().__init__()
        self.projection = nn.Sequential(
            nn.Linear(audio_embedding_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
            nn.Dropout(dropout_rate)
        )
        
    def forward(self, audio_features: torch.Tensor) -> torch.Tensor:
        return self.projection(audio_features)

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
        
    def forward(
        self,
        x: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        batch_size, seq_length, hidden_size = x.shape
        
        # 线性变换
        q = self.query(x)
        k = self.key(x)
        v = self.value(x)
        
        # 重塑为多头形式
        q = q.view(batch_size, seq_length, self.num_heads, self.head_size).transpose(1, 2)
        k = k.view(batch_size, seq_length, self.num_heads, self.head_size).transpose(1, 2)
        v = v.view(batch_size, seq_length, self.num_heads, self.head_size).transpose(1, 2)
        
        # 计算注意力分数
        scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_size)
        
        # 应用掩码
        if mask is not None:
            # 扩展掩码维度以匹配注意力分数
            mask = mask.unsqueeze(1).expand(batch_size, self.num_heads, seq_length, seq_length)
            scores = scores.masked_fill(mask == 0, float('-inf'))
        
        # 应用softmax
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        # 计算输出
        output = torch.matmul(attention_weights, v)
        output = output.transpose(1, 2).contiguous().view(batch_size, seq_length, hidden_size)
        
        return self.output(output)

class TransformerBlock(nn.Module):
    """Transformer块"""
    def __init__(self, hidden_size: int, num_heads: int, dropout_rate: float = 0.1):
        super().__init__()
        self.attention = MultiHeadAttention(hidden_size, num_heads, dropout_rate)
        self.feed_forward = nn.Sequential(
            nn.Linear(hidden_size, hidden_size * 4),
            nn.GELU(),
            nn.Dropout(dropout_rate),
            nn.Linear(hidden_size * 4, hidden_size),
            nn.Dropout(dropout_rate)
        )
        self.norm1 = nn.LayerNorm(hidden_size)
        self.norm2 = nn.LayerNorm(hidden_size)
        
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        # 自注意力层
        attention_output = self.attention(self.norm1(x), mask)
        x = x + attention_output
        
        # 前馈网络
        feed_forward_output = self.feed_forward(self.norm2(x))
        x = x + feed_forward_output
        
        return x

class BiMLM(nn.Module):
    """双向Transformer序列推荐模型"""
    def __init__(
        self,
        num_items: int,
        audio_embedding_size: int = 512,
        hidden_size: int = 64,
        num_heads: int = 4,
        num_layers: int = 2,
        dropout_rate: float = 0.1,
        max_seq_length: int = 50,
        mask_prob: float = 0.15
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.max_seq_length = max_seq_length
        self.mask_prob = mask_prob
        self.num_items = num_items
        self.mask_token_id = num_items + 1
        self.audio_embedding_size = audio_embedding_size
        
        # 编码层
        self.item_embedding = ItemEmbedding(num_items, hidden_size)
        self.position_embedding = PositionalEmbedding(max_seq_length, hidden_size)
        self.audio_embedding = AudioEmbedding(audio_embedding_size, hidden_size, dropout_rate)
        
        # Transformer层
        self.transformer_layers = nn.ModuleList([
            TransformerBlock(hidden_size, num_heads, dropout_rate)
            for _ in range(num_layers)
        ])
        
        self.dropout = nn.Dropout(dropout_rate)
        self.layer_norm = nn.LayerNorm(hidden_size)
        
        # 输出层
        self.output_layer = nn.Linear(hidden_size, num_items + 2)
        
        # 初始化音频嵌入字典
        self.audio_embeddings = {}
        
    def load_audio_embeddings(self, audio_embeddings_dir: str):
        """加载音频嵌入向量
        
        Args:
            audio_embeddings_dir: 音频嵌入向量目录
        """
        self.audio_embeddings = {}
        all_embeddings = []
        
        for file_name in os.listdir(audio_embeddings_dir):
            if file_name.endswith('.npy'):
                song_id = int(file_name.split('.')[0])
                embedding = np.load(os.path.join(audio_embeddings_dir, file_name))
                self.audio_embeddings[song_id] = torch.tensor(embedding, dtype=torch.float32)
                all_embeddings.append(embedding)
        
        if all_embeddings:
            # 计算平均嵌入向量作为默认值
            self.mean_audio_embedding = torch.tensor(
                np.mean(all_embeddings, axis=0),
                dtype=torch.float32
            )
        else:
            # 如果没有嵌入向量，使用零向量作为默认值
            self.mean_audio_embedding = torch.zeros(
                self.audio_embedding_size,
                dtype=torch.float32
            )
            
        logger.info(f"Loaded {len(self.audio_embeddings)} audio embeddings")
        
    def _create_masked_input(self, input_ids: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """创建掩码输入"""
        batch_size, seq_length = input_ids.shape
        mask_labels = torch.zeros_like(input_ids)
        
        # 创建随机掩码
        mask = torch.rand(input_ids.shape) < self.mask_prob
        mask = mask & (input_ids != 0)  # 不掩码填充标记
        
        # 创建掩码后的输入
        masked_input_ids = input_ids.clone()
        masked_input_ids[mask] = self.mask_token_id
        
        # 保存掩码标签
        mask_labels[mask] = input_ids[mask]
        
        return masked_input_ids, mask_labels
        
    def forward(
        self,
        input_ids: torch.Tensor,
        ratings: torch.Tensor,
        audio_embeddings: Dict[int, torch.Tensor],
        training: bool = False
    ) -> Tuple[torch.Tensor, Optional[torch.Tensor]]:
        batch_size, seq_length = input_ids.shape
        
        # 创建掩码输入
        if training:
            input_ids, mask_labels = self._create_masked_input(input_ids)
        else:
            mask_labels = None
        
        # 获取物品嵌入
        item_embeddings = self.item_embedding(input_ids)
        
        # 获取位置编码
        position_embeddings = self.position_embedding(seq_length, input_ids.device)
        
        # 获取音频特征
        audio_features = []
        for i in range(batch_size):
            seq_audio_features = []
            for j in range(seq_length):
                song_id = input_ids[i, j].item()
                if song_id in audio_embeddings:
                    audio_feat = audio_embeddings[song_id]
                    if len(audio_feat.shape) > 1:
                        audio_feat = audio_feat[0]
                    audio_feat = audio_feat.view(-1)
                    audio_feat = F.normalize(audio_feat, p=2, dim=0)
                else:
                    audio_feat = torch.zeros(self.audio_embedding_size, device=input_ids.device)
                seq_audio_features.append(audio_feat)
            seq_audio_features = torch.stack(seq_audio_features)
            audio_features.append(seq_audio_features)
        audio_features = torch.stack(audio_features)
        
        # 投影音频特征
        audio_embeddings = self.audio_embedding(audio_features)
        
        # 合并嵌入
        embeddings = item_embeddings + position_embeddings + audio_embeddings
        embeddings = self.layer_norm(embeddings)
        embeddings = self.dropout(embeddings)
        
        # 创建注意力掩码
        attention_mask = (input_ids != 0).unsqueeze(1)
        attention_mask = attention_mask.expand(batch_size, seq_length, seq_length)
        
        # 应用Transformer编码器
        hidden_states = embeddings
        for layer in self.transformer_layers:
            hidden_states = layer(hidden_states, attention_mask)
        
        # 计算预测分数
        scores = self.output_layer(hidden_states)
        
        # 数值稳定性检查
        if torch.isnan(scores).any():
            print("Warning: NaN detected in scores")
            scores = torch.nan_to_num(scores, nan=0.0)
        
        # 对分数进行缩放
        scores = scores / math.sqrt(self.hidden_size)
        
        # 添加温度缩放
        temperature = 0.1
        scores = scores / temperature
        
        # 计算掩码损失
        mask_loss = None
        if training and mask_labels is not None:
            mask_loss = F.cross_entropy(
                scores.view(-1, scores.size(-1)),
                mask_labels.view(-1),
                ignore_index=0
            )
        
        return scores, mask_loss 