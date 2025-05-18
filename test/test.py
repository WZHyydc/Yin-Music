


#
# # # 加载音频文件
# # audio, sr = librosa.load("./胡歌-忘记时间.mp3", sr=16000, mono=True)
# #
# # # 提取音频嵌入
# # embeddings, timestamps = openl3.get_audio_embedding(audio, sr, input_repr="mel128", content_type="music", embedding_size=512)
# #
# #
# # # 保存嵌入向量
# # np.save("audio_embedding.npy", embeddings)
#
# # 加载嵌入向量
# embeddings = np.load("audio_embedding.npy")
#
# # 打印嵌入向量的形状
# print("嵌入向量的形状:", embeddings.shape)
#
# # 打印嵌入向量的元素
# print("嵌入向量的前5个元素:", embeddings[:2718])


import librosa
import openl3
import numpy as np


def extract_embeddings(audio_path, target_duration=30, sr=8000, embedding_size=512):
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

    return embeddings


# 提取音频嵌入
audio_embeddings = extract_embeddings("胡歌-忘记时间.mp3")

# 输出嵌入向量的形状，查看是否符合预期
print(f"优化后的音频嵌入形状: {audio_embeddings.shape}")

# 保存嵌入向量
np.save("audio_embedding_optimized.npy", audio_embeddings)

# 加载嵌入向量
loaded_embeddings = np.load("audio_embedding_optimized.npy")


