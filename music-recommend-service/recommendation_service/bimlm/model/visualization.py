import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
from .model import BiMLM

class ModelVisualizer:
    """BiMLM 模型可视化工具"""
    def __init__(self, model: BiMLM):
        self.model = model
        
    def visualize_architecture(self):
        """可视化模型架构"""
        # 创建图形
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # 绘制模型组件
        components = [
            "输入层",
            "物品嵌入层",
            "位置编码层",
            "音频特征投影层",
            "Transformer层",
            "输出层"
        ]
        
        y_pos = np.arange(len(components))
        ax.barh(y_pos, [1] * len(components))
        ax.set_yticks(y_pos)
        ax.set_yticklabels(components)
        ax.set_xlabel("组件大小")
        ax.set_title("BiMLM 模型架构")
        
        plt.tight_layout()
        plt.show()
        
    def visualize_attention_weights(
        self,
        input_sequence: torch.Tensor,
        ratings: torch.Tensor
    ):
        """
        可视化注意力权重
        
        Args:
            input_sequence: 输入序列
            ratings: 评分序列
        """
        # 获取物品嵌入
        item_embeddings = self.model.item_embedding(input_sequence)
        
        # 获取位置编码
        position_ids = torch.arange(input_sequence.size(1), device=input_sequence.device).unsqueeze(0)
        position_embeddings = self.model.position_embedding(position_ids)
        
        # 获取音频特征
        audio_features = []
        for i in range(input_sequence.size(0)):
            seq_audio_features = []
            for j in range(input_sequence.size(1)):
                song_id = input_sequence[i, j].item()
                if song_id in self.model.audio_embeddings:
                    audio_feat = self.model.audio_projection(self.model.audio_embeddings[song_id])
                else:
                    audio_feat = torch.zeros(self.model.hidden_size, device=input_sequence.device)
                seq_audio_features.append(audio_feat)
            audio_features.append(torch.stack(seq_audio_features))
        audio_features = torch.stack(audio_features)
        
        # 合并嵌入
        embeddings = item_embeddings + position_embeddings + audio_features
        
        # 获取注意力权重
        attention_weights = []
        for layer in self.model.transformer_layers:
            attention_output = layer.attention(
                layer.norm1(embeddings),
                mask=None,
                ratings=ratings,
                bidirectional=True
            )
            attention_weights.append(attention_output.detach().cpu().numpy())
        
        # 可视化每个层的注意力权重
        num_layers = len(attention_weights)
        fig, axes = plt.subplots(1, num_layers, figsize=(5 * num_layers, 5))
        
        for i, weights in enumerate(attention_weights):
            sns.heatmap(
                weights[0],
                ax=axes[i],
                cmap="YlOrRd",
                xticklabels=False,
                yticklabels=False
            )
            axes[i].set_title(f"Layer {i+1} Attention Weights")
        
        plt.tight_layout()
        plt.show()
        
    def visualize_embeddings(self, item_ids: List[int]):
        """
        可视化物品嵌入
        
        Args:
            item_ids: 物品ID列表
        """
        # 获取物品嵌入
        embeddings = self.model.item_embedding(torch.tensor(item_ids))
        
        # 使用PCA降维
        from sklearn.decomposition import PCA
        pca = PCA(n_components=2)
        embeddings_2d = pca.fit_transform(embeddings.detach().cpu().numpy())
        
        # 绘制散点图
        plt.figure(figsize=(10, 10))
        plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1])
        
        # 添加标签
        for i, item_id in enumerate(item_ids):
            plt.annotate(
                str(item_id),
                (embeddings_2d[i, 0], embeddings_2d[i, 1])
            )
        
        plt.title("物品嵌入可视化 (PCA降维)")
        plt.xlabel("主成分1")
        plt.ylabel("主成分2")
        plt.show()
        
    def visualize_audio_features(self, audio_embeddings: Dict[int, torch.Tensor]):
        """
        可视化音频特征
        
        Args:
            audio_embeddings: 音频嵌入向量字典
        """
        # 获取音频特征
        features = []
        for song_id in audio_embeddings:
            feature = self.model.audio_projection(audio_embeddings[song_id])
            features.append(feature.detach().cpu().numpy())
        features = np.array(features)
        
        # 使用PCA降维
        from sklearn.decomposition import PCA
        pca = PCA(n_components=2)
        features_2d = pca.fit_transform(features)
        
        # 绘制散点图
        plt.figure(figsize=(10, 10))
        plt.scatter(features_2d[:, 0], features_2d[:, 1])
        
        # 添加标签
        for i, song_id in enumerate(audio_embeddings.keys()):
            plt.annotate(
                str(song_id),
                (features_2d[i, 0], features_2d[i, 1])
            )
        
        plt.title("音频特征可视化 (PCA降维)")
        plt.xlabel("主成分1")
        plt.ylabel("主成分2")
        plt.show()
        
    def visualize_masking_effect(self, input_sequence: torch.Tensor):
        """
        可视化掩码效果
        
        Args:
            input_sequence: 输入序列
        """
        # 创建掩码输入
        masked_input, mask_labels = self.model._create_masked_input(input_sequence)
        
        # 可视化原始序列和掩码序列
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
        
        # 原始序列
        sns.heatmap(
            input_sequence.cpu().numpy(),
            ax=ax1,
            cmap="YlOrRd",
            xticklabels=False,
            yticklabels=False
        )
        ax1.set_title("原始序列")
        
        # 掩码序列
        sns.heatmap(
            masked_input.cpu().numpy(),
            ax=ax2,
            cmap="YlOrRd",
            xticklabels=False,
            yticklabels=False
        )
        ax2.set_title("掩码序列")
        
        plt.tight_layout()
        plt.show() 