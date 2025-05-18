import os
import librosa
import openl3
import numpy as np
import concurrent.futures
from sqlalchemy.orm import Session
from models import Song, get_db
from config import AUDIO_FILES_DIR, AUDIO_EMBEDDINGS_DIR

# 添加全局变量用于存储最近成功的embedding
last_successful_embedding = None
NOISE_SCALE = 1e-4  # 高斯噪声的标准差

def add_noise(embedding, noise_scale=NOISE_SCALE):
    """
    向embedding添加微小的高斯噪声
    
    Args:
        embedding: 原始embedding向量
        noise_scale: 噪声的标准差
        
    Returns:
        添加噪声后的embedding向量
    """
    noise = np.random.normal(0, noise_scale, embedding.shape)
    return embedding + noise

def extract_embeddings(audio_path, target_duration=30, sr=8000, embedding_size=512):
    """
    从音频文件中提取嵌入向量，限制音频长度为 30 秒，不足部分填充。
    最后将所有帧的嵌入向量进行平均，返回一个形状为 (512,) 的嵌入向量。
    """
    global last_successful_embedding
    
    try:
        # 加载音频文件并调整采样频率
        audio, _ = librosa.load(audio_path, sr=sr, mono=True)
        
        # 计算目标音频长度的样本数
        target_samples = target_duration * sr
        
        # 如果音频长度不足 30 秒，进行填充
        if len(audio) < target_samples:
            padding = target_samples - len(audio)
            audio = np.pad(audio, (0, padding), 'constant')
        else:
            # 如果音频超过 30 秒，只取前 30 秒
            audio = audio[:target_samples]
        
        # 提取音频的嵌入
        embeddings, timestamps = openl3.get_audio_embedding(
            audio, sr, input_repr="mel128", content_type="music", embedding_size=embedding_size
        )
        
        # 确保嵌入向量的维度正确
        if embeddings.shape[1] != embedding_size:
            print(f"警告：嵌入向量维度不正确，期望 {embedding_size}，实际 {embeddings.shape[1]}，正在调整...")
            # 如果维度不匹配，使用最近成功的嵌入向量
            if last_successful_embedding is not None:
                return add_noise(last_successful_embedding)
            else:
                return add_noise(np.zeros(embedding_size))
        
        # 对所有帧的嵌入向量取平均
        aggregated_embedding = np.mean(embeddings, axis=0)
        
        # 确保最终输出的嵌入向量是一维的，且维度为512
        if len(aggregated_embedding.shape) > 1:
            aggregated_embedding = aggregated_embedding.flatten()
        if aggregated_embedding.shape[0] != embedding_size:
            print(f"警告：聚合后的嵌入向量维度不正确，期望 {embedding_size}，实际 {aggregated_embedding.shape[0]}，正在调整...")
            if last_successful_embedding is not None:
                return add_noise(last_successful_embedding)
            else:
                return add_noise(np.zeros(embedding_size))
        
        # 更新最近成功的embedding
        last_successful_embedding = aggregated_embedding
        return aggregated_embedding
        
    except Exception as e:
        print(f"提取嵌入向量时发生错误: {str(e)}")
        if last_successful_embedding is not None:
            # 使用最近成功的embedding并添加微小扰动
            print(f"使用前一个成功的embedding（添加微小扰动）")
            return add_noise(last_successful_embedding)
        else:
            # 如果没有可用的历史embedding，返回零向量+微小扰动
            print(f"没有可用的历史embedding，返回零向量+微小扰动")
            return add_noise(np.zeros(embedding_size))

def get_song_id_mapping(db: Session):
    """
    从数据库获取歌曲URL到ID的映射关系
    """
    songs = db.query(Song).all()
    # 创建文件名到song_id的映射
    # 从url中提取文件名（最后一个/后面的部分）
    return {os.path.basename(song.url): song.id for song in songs}

def process_single_audio_file_named_by_song_id(audio_file_path_named_by_song_id, output_dir = AUDIO_EMBEDDINGS_DIR):
    """
    处理单个音频文件，并将嵌入向量保存到磁盘。
    如果音频处理失败，extract_embeddings会返回零向量+微小扰动/使用前一个成功的embedding+微小扰动。
    """
    # 得到带后缀的歌曲文件名
    file_name = os.path.basename(audio_file_path_named_by_song_id)
    # 获取文件名（不含扩展名）
    song_id = os.path.splitext(file_name)[0]
    
    # 提取音频嵌入（如果失败会返回零向量+微小扰动）
    embeddings = extract_embeddings(audio_file_path_named_by_song_id)
    
    # 使用文件名作为输出文件名
    output_file = os.path.join(output_dir, f"{song_id}.npy")
    np.save(output_file, embeddings)
    print(f"已处理并保存: {audio_file_path_named_by_song_id}")

    # 删除原始音频文件
    os.remove(audio_file_path_named_by_song_id)
    print(f"已删除原始音频文件: {audio_file_path_named_by_song_id}")

def process_single_audio(audio_file, output_dir, song_id_mapping):
    """
    处理单个音频文件，将其重命名为song_id，然后提取嵌入向量。
    
    Args:
        audio_file: 原始音频文件路径
        output_dir: 输出目录
        song_id_mapping: 文件名到song_id的映射字典
    """
    # 获取原始文件名
    original_filename = os.path.basename(audio_file)
    
    # 从映射中获取song_id
    if original_filename not in song_id_mapping:
        print(f"警告：找不到歌曲 {original_filename} 的ID映射，跳过处理")
        return
        
    song_id = song_id_mapping[original_filename]
    
    # 创建临时文件路径（使用song_id作为文件名）
    temp_dir = os.path.join(os.path.dirname(audio_file), "temp")
    os.makedirs(temp_dir, exist_ok=True)
    temp_file = os.path.join(temp_dir, f"{song_id}{os.path.splitext(original_filename)[1]}")
    
    try:
        # 复制并重命名文件
        import shutil
        shutil.copy2(audio_file, temp_file)
        
        # 处理重命名后的文件
        process_single_audio_file_named_by_song_id(temp_file, output_dir)
        
    except Exception as e:
        print(f"处理文件 {original_filename} 时发生错误: {str(e)}")
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if os.path.exists(temp_dir) and not os.listdir(temp_dir):
            os.rmdir(temp_dir)

def process_batch(audio_files, output_dir, song_id_mapping):
    """
    处理一个批次的音频文件，并将嵌入向量保存到磁盘。
    """
    for audio_file in audio_files:
        process_single_audio(audio_file, output_dir, song_id_mapping)

def batch_process_audio_files(input_dir, output_dir, batch_size=10):
    """
    将音频文件分批次处理，使用并行化加速处理。
    """
    # 创建输出目录
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 获取数据库会话
    db = next(get_db())
    try:
        # 获取歌曲ID映射
        song_id_mapping = get_song_id_mapping(db)
        
        # 获取目录下所有音频文件
        audio_files = [os.path.join(input_dir, f) for f in os.listdir(input_dir) 
                      if f.lower().endswith(('.mp3', '.wav', '.flac'))]

        # 分批次处理音频文件
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # 分割音频文件列表为批次
            batches = [audio_files[i:i + batch_size] for i in range(0, len(audio_files), batch_size)]
            
            # 并行处理每个批次
            futures = [executor.submit(process_batch, batch, output_dir, song_id_mapping) 
                      for batch in batches]

            # 等待所有任务完成
            concurrent.futures.wait(futures)
    finally:
        db.close()

if __name__ == "__main__":
    # 输入文件夹路径（包含音频文件）
    input_dir = AUDIO_FILES_DIR
    
    # 输出文件夹路径（存储嵌入向量）
    output_dir = AUDIO_EMBEDDINGS_DIR
    
    # 设置批次大小，例如每次处理 10 个音频文件
    batch_size = 10
    
    # 批量处理音频文件
    batch_process_audio_files(input_dir, output_dir, batch_size)
