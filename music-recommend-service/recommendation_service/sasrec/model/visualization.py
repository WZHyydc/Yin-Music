import torch
import torchviz
from graphviz import Digraph
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List
from sklearn.manifold import TSNE
from sasrec.model.model import SASRec
import os
import platform

class ModelVisualizer:
    def __init__(self, model: SASRec):
        self.model = model
        # 创建可视化结果保存目录
        self.vis_dir = os.path.join('visualization')
        os.makedirs(self.vis_dir, exist_ok=True)
        
        # 设置字体
        self._setup_fonts()
        
    def _setup_fonts(self):
        """
        设置matplotlib字体
        """
        system = platform.system()
        if system == 'Darwin':  # macOS
            plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Heiti TC', 'STHeiti', 'SimHei', 'sans-serif']
        elif system == 'Windows':
            plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'sans-serif']
        else:  # Linux
            plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'SimHei', 'sans-serif']
        
        plt.rcParams['axes.unicode_minus'] = False
        
    def visualize_architecture(self, input_shape=(1, 50)):
        """
        可视化模型架构 - 论文风格
        
        Args:
            input_shape: 输入张量的形状，默认为(1, 50)
        """
        # 创建图形
        plt.figure(figsize=(12, 8))
        
        # 获取模型配置信息
        num_layers = len(self.model.transformer_layers)
        num_heads = self.model.transformer_layers[0].attention.num_heads
        hidden_size = self.model.hidden_size
        
        # 绘制模型架构
        # 1. 输入层
        plt.subplot(411)
        plt.text(0.5, 0.5, f'Input Layer\n(Item ID + Position + Audio)\nHidden Size: {hidden_size}', 
                ha='center', va='center', fontsize=12)
        plt.axis('off')
        
        # 2. Transformer编码器层
        plt.subplot(412)
        plt.text(0.5, 0.5, f'Transformer Encoder\n(Multi-head Attention + FFN) x {num_layers}', 
                ha='center', va='center', fontsize=12)
        plt.axis('off')
        
        # 3. 注意力机制
        plt.subplot(413)
        plt.text(0.5, 0.5, f'Multi-head Attention\n({num_heads} heads)', 
                ha='center', va='center', fontsize=12)
        plt.axis('off')
        
        # 4. 输出层
        plt.subplot(414)
        plt.text(0.5, 0.5, 'Output Layer\n(Item Prediction Scores)', 
                ha='center', va='center', fontsize=12)
        plt.axis('off')
        
        # 调整子图之间的间距
        plt.subplots_adjust(hspace=0.3)
        
        # 保存图片
        output_path = os.path.join(self.vis_dir, "model_architecture.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"模型架构图已保存为 {output_path}")
        
        # 创建模型参数统计图
        self._visualize_model_parameters()
        
    def _visualize_model_parameters(self):
        """
        可视化模型参数统计
        """
        # 计算各层参数数量
        total_params = 0
        layer_params = {}
        
        for name, param in self.model.named_parameters():
            if param.requires_grad:
                params = param.numel()
                total_params += params
                layer_name = name.split('.')[0]
                if layer_name not in layer_params:
                    layer_params[layer_name] = 0
                layer_params[layer_name] += params
        
        # 绘制参数分布饼图
        plt.figure(figsize=(10, 6))
        plt.pie(layer_params.values(), labels=layer_params.keys(), autopct='%1.1f%%')
        plt.title('Model Parameters Distribution')
        
        # 保存图片
        output_path = os.path.join(self.vis_dir, "model_parameters.png")
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"模型参数分布图已保存为 {output_path}")
        
        # 打印参数统计信息
        print("\nModel Parameters Statistics:")
        print(f"Total Parameters: {total_params:,}")
        for layer, params in layer_params.items():
            print(f"{layer}: {params:,} ({params/total_params*100:.1f}%)")
        
    def visualize_attention_weights(self, input_sequence: torch.Tensor, ratings: torch.Tensor):
        """
        可视化注意力权重
        
        Args:
            input_sequence: 输入序列
            ratings: 评分序列
        """
        # 获取物品嵌入
        item_embeddings = self.model.item_embedding(input_sequence)  # [batch_size, seq_length, hidden_size]
        
        # 获取位置编码
        position_ids = torch.arange(input_sequence.size(1), device=input_sequence.device).unsqueeze(0)
        position_embeddings = self.model.position_embedding(position_ids)  # [1, seq_length, hidden_size]
        
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
        audio_features = torch.stack(audio_features)  # [batch_size, seq_length, hidden_size]
        
        # 合并嵌入
        embeddings = item_embeddings + position_embeddings + audio_features
        
        # 获取注意力权重
        attention_weights = []
        for layer in self.model.transformer_layers:
            attention_output = layer.attention(
                layer.norm1(embeddings),
                mask=None,
                ratings=ratings
            )
            attention_weights.append(attention_output.detach().numpy())
        
        # 绘制每一层的注意力权重热力图
        for i, weights in enumerate(attention_weights):
            plt.figure(figsize=(10, 8))
            sns.heatmap(weights[0], cmap="YlOrRd")
            plt.title(f"Attention Weights - Layer {i+1}")
            plt.xlabel("Key Position")
            plt.ylabel("Query Position")
            output_path = os.path.join(self.vis_dir, f"attention_weights_layer_{i+1}.png")
            plt.savefig(output_path)
            plt.close()
            
        print(f"注意力权重图已保存到 {self.vis_dir} 目录")
        
    def visualize_embeddings(self, item_ids: List[int]):
        """
        可视化物品嵌入向量
        
        Args:
            item_ids: 物品ID列表
        """
        # 获取物品嵌入
        embeddings = self.model.item_embedding(torch.tensor(item_ids, dtype=torch.long))
        
        # 使用t-SNE降维
        tsne = TSNE(n_components=2)
        embeddings_2d = tsne.fit_transform(embeddings.detach().numpy())
        
        # 绘制散点图
        plt.figure(figsize=(10, 8))
        plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1])
        plt.title("Item Embeddings Visualization")
        output_path = os.path.join(self.vis_dir, "item_embeddings.png")
        plt.savefig(output_path)
        plt.close()
        
        print(f"物品嵌入向量图已保存为 {output_path}")
        
    def visualize_audio_features(self, audio_embeddings: Dict[int, torch.Tensor]):
        """
        可视化音频特征
        
        Args:
            audio_embeddings: 音频嵌入向量字典
        """
        # 将音频嵌入向量转换为numpy数组
        embeddings = np.array([emb.detach().numpy() for emb in audio_embeddings.values()])
        
        # 使用t-SNE降维
        tsne = TSNE(n_components=2)
        embeddings_2d = tsne.fit_transform(embeddings)
        
        # 绘制散点图
        plt.figure(figsize=(10, 8))
        plt.scatter(embeddings_2d[:, 0], embeddings_2d[:, 1])
        plt.title("Audio Features Visualization")
        output_path = os.path.join(self.vis_dir, "audio_features.png")
        plt.savefig(output_path)
        plt.close()
        
        print(f"音频特征图已保存为 {output_path}")

def main():
    # 创建模型实例
    model = SASRec(
        num_items=1000,
        audio_embedding_size=512,
        hidden_size=64,
        num_heads=4,
        num_layers=2
    )
    
    # 初始化音频嵌入
    model.audio_embeddings = {i: torch.randn(512) for i in range(1, 1001)}
    
    # 创建可视化器
    visualizer = ModelVisualizer(model)
    
    # 可视化模型架构
    visualizer.visualize_architecture()
    
    # 创建示例输入
    input_sequence = torch.randint(1, 1000, (1, 50), dtype=torch.long)  # 修改为Long类型
    ratings = torch.zeros(1, 50, dtype=torch.float32)  # 评分使用float类型
    
    # 可视化注意力权重
    visualizer.visualize_attention_weights(input_sequence, ratings)
    
    # 可视化物品嵌入
    item_ids = list(range(1, 101))
    visualizer.visualize_embeddings(item_ids)
    
    # 可视化音频特征
    audio_embeddings = {i: torch.randn(512) for i in range(1, 101)}
    visualizer.visualize_audio_features(audio_embeddings)

if __name__ == "__main__":
    main() 