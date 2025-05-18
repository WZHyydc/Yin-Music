# 音乐推荐服务

基于SASRec模型的音乐推荐服务，使用用户历史行为序列进行推荐。

## 项目结构

```
music-recommend-service/
├── data/                           # 数据目录
│   ├── audio_embeddings_output/    # 音频嵌入向量输出目录
│   │   └── embeddings.npy         # 音频嵌入向量文件
│   ├── audio_files/               # 音频文件目录
│   │   └── *.mp3                 # 音频文件
│   └── model_output/              # 模型输出目录
│       ├── model.pth             # 模型权重文件
│       └── config.json           # 模型配置文件
├── recommendation_service/         # 推荐服务主目录
│   ├── sasrec/                    # SASRec模型实现
│   │   ├── model/                 # 模型定义
│   │   │   ├── predictor.py       # 预测器实现
│   │   │   └── extract_songs_embeddings.py  # 音频嵌入向量提取
│   │   └── train.py               # 模型训练脚本
│   ├── models.py                  # 数据库模型定义
│   ├── config.py                  # 配置文件
│   └── run_recommendation.py      # 推荐生成脚本
└── README.md                      # 项目说明文档
```

## 功能特性

- 基于用户历史行为序列的推荐
- 支持用户播放历史、收藏和评分数据的整合
- 使用SASRec模型进行序列建模
- 支持音频文件嵌入向量的提取和存储
- 使用预训练音频模型提取音频特征

## 环境要求

- Python 3.12+
- PyTorch 2.0+
- SQLAlchemy 2.0+
- PyMySQL 1.1+
- NumPy 1.26+
- Pandas 2.0+
- librosa 0.10+
- torchaudio 2.0+
- openl3 0.4+

### 依赖安装

1. 创建虚拟环境：
```bash
# 使用 venv
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 或使用 conda
conda create -n music-recommend python=3.12
conda activate music-recommend
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

### 系统要求

- 操作系统：Linux/macOS/Windows
- 内存：建议 8GB 以上
- 存储：建议 20GB 以上可用空间
- GPU：推荐 NVIDIA GPU（用于音频特征提取和模型训练）

## 安装

1. 克隆仓库：
```bash
git clone [repository_url]
cd music-recommend-service
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 使用说明

### 1. 音频嵌入向量提取

首先需要提取音频文件的嵌入向量：

```bash
python -m recommendation_service.sasrec.model.extract_songs_embeddings
```

这将会：
- 读取 `data/audio_files` 目录下的音频文件
- 使用预训练模型提取音频特征
- 将嵌入向量保存到 `data/audio_embeddings_output/embeddings.npy` 文件
- 支持批量处理音频文件
- 自动跳过已处理的文件
- 提供处理进度显示

### 2. 模型训练

训练SASRec模型：

```bash
python -m recommendation_service.sasrec.train
```

### 3. 生成推荐

运行推荐生成脚本：

```bash
python -m recommendation_service.run_recommendation
```

## 配置说明

在 `recommendation_service/config.py` 中可以配置以下参数：

- 数据库连接信息
- 模型参数
- 推荐参数
- 音频处理参数
  - 音频采样率
  - 音频片段长度
  - 批处理大小
  - 设备选择（CPU/GPU）

## 数据格式

### 音频嵌入向量

音频嵌入向量文件格式为 `.npy`，包含所有音频文件的特征向量，维度为 [n_songs, embedding_dim]。

### 用户特征

用户特征包括：
- 最近播放序列
- 收藏歌曲列表
- 歌曲评分数据

## 注意事项

1. 确保音频文件已正确放置在 `data/audio_files` 目录下
2. 运行推荐生成前需要先完成音频嵌入向量的提取
3. 定期更新用户特征数据以保持推荐的时效性
4. 音频文件处理可能需要较大的内存和计算资源
5. 建议使用GPU进行音频特征提取

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

[许可证类型] 