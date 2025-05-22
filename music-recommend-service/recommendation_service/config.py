import os
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent

# 数据目录
DATA_DIR = ROOT_DIR / 'data'
AUDIO_FILES_DIR = DATA_DIR / 'audio_files'
AUDIO_EMBEDDINGS_DIR = DATA_DIR / 'audio_embeddings_output'
MODEL_OUTPUT_DIR = DATA_DIR / 'model_output'

# 确保目录存在
for dir_path in [DATA_DIR, AUDIO_FILES_DIR, AUDIO_EMBEDDINGS_DIR, MODEL_OUTPUT_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# MinIO配置
MINIO_CONFIG = {
    # 'endpoint': os.getenv('MINIO_ENDPOINT', 'localhost:9000'),
    'endpoint': 'http://YinMinio:9000',
    'access_key': os.getenv('MINIO_ACCESS_KEY', 'root'),
    'secret_key': os.getenv('MINIO_SECRET_KEY', '123456789'),
    'secure': os.getenv('MINIO_SECURE', 'false').lower() == 'true',
    'bucket_name': os.getenv('MINIO_BUCKET', 'user01')
}

# 数据库配置
DB_CONFIG = {
    # 'host': os.getenv('DB_HOST', 'localhost'),
    'host': os.getenv('DB_HOST', 'YinMysql'),
    'port': int(os.getenv('DB_PORT', 3306)),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'root'),
    'database': os.getenv('DB_NAME', 'tp_music'),
    'charset': 'utf8mb4'
}

# 模型配置
MODEL_CONFIG = {
    'version': 'sasrec',  # 模型版本
    'sequence_length': 50,  # 总序列长度
    'favorite_ratio': 0.3,  # 收藏序列占总序列的比例
    'playhistory_ratio': 0.7,  # 播放历史序列占总序列的比例
    'num_items': 113, # 歌曲数量 歌曲ID从1-num_items


    # 数据相关
    'user_data_path': str(DATA_DIR / 'user_data' / 'user_data.csv'),
    'audio_embeddings_dir': str(AUDIO_EMBEDDINGS_DIR),
    'model_dir': str(MODEL_OUTPUT_DIR),
    # 根据需要选择对应的模型名字_best_model.pth文件
    'model_path': str(MODEL_OUTPUT_DIR / 'best_model.pth'),
    'history_path': str(MODEL_OUTPUT_DIR / 'history.json'),
    'checkpoint_dir': str(MODEL_OUTPUT_DIR / 'checkpoints'),
    
    # 模型架构
    'hidden_size': 64,
    'num_heads': 4,
    'num_layers': 3,
    'dropout_rate': 0.001,
    'max_seq_length': 50,
    
    # 训练参数
    'batch_size': 128,
    'learning_rate': 0.001,
    'weight_decay': 1e-4,
    'num_epochs': 20,
    
    # 音频处理
    'audio_sample_rate': 16000,
    'audio_duration': 30,  # 秒
    'audio_hop_length': 512,
    'audio_n_mels': 128,
    'audio_n_fft': 2048,
    'audio_embedding_size': 512,
    
    # 设备配置
    'device': 'cuda' if os.getenv('USE_GPU', 'true').lower() == 'true' else 'cpu',
    'early_stopping_patience': 3,  # 提前停止的耐心值
}

# 推荐配置
RECOMMEND_CONFIG = {
    'recommendation_model': 'sasrec',  # 推荐模型名称
    'device': 'cuda' if os.getenv('USE_GPU', 'true').lower() == 'true' else 'cpu',
    'top_k': 10,  # 推荐结果数量
    'min_sequence_length': 5,  # 最小序列长度
    'max_sequence_length': 50,  # 最大序列长度
    'update_interval': 3600,  # 更新间隔（秒）
} 