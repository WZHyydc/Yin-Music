import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import desc, func
from models import PlayHistory, UserFeatures, UserRecommendations, Song, get_db
from sasrec.model.predictor import SASRecPredictor
from sasrec.model.extract_songs_embeddings import process_single_audio_file_named_by_song_id
from config import MODEL_CONFIG, RECOMMEND_CONFIG, MINIO_CONFIG, AUDIO_FILES_DIR, AUDIO_EMBEDDINGS_DIR
from minio import Minio
import numpy as np

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_user_playSequences(db) -> Dict[int, List[int]]:
    """
    获取用户最近的播放序列
    
    Args:
        db: 数据库会话
        
    Returns:
        Dict[int, List[int]]: 用户ID到播放序列的映射
    """
    user_sequences = {}
    
    try:
        # 获取所有活跃用户（最近30天有播放记录的用户）
        thirty_days_ago = datetime.now() - timedelta(days=30)
        active_users = db.query(PlayHistory.user_id)\
            .filter(PlayHistory.play_time >= thirty_days_ago)\
            .distinct()\
            .all()
            
        logger.info(f"找到 {len(active_users)} 个活跃用户")
        
        for user_id, in active_users:
            # 获取用户最近的播放记录
            recent_plays = db.query(PlayHistory.song_id)\
                .filter(PlayHistory.user_id == user_id)\
                .order_by(desc(PlayHistory.play_time))\
                .limit(MODEL_CONFIG['sequence_length'])\
                .all()
                
            # 转换为列表并反转（从旧到新）
            sequence = [song_id for song_id, in recent_plays][::-1]
            if sequence:
                user_sequences[user_id] = sequence
                
        logger.info(f"成功获取 {len(user_sequences)} 个用户的播放序列")
        return user_sequences
        
    except Exception as e:
        logger.error(f"获取用户序列时发生错误: {str(e)}")
        raise

def get_user_favorites(db, user_id: int) -> List[int]:
    """
        获取用户收藏的歌曲列表
    """
    try:
        # 从collect表获取用户收藏的歌曲
        favorites = db.execute("""
            SELECT song_id 
            FROM collect 
            WHERE user_id = :user_id AND type = 0
        """, {"user_id": user_id}).fetchall()
        return [f[0] for f in favorites]
    except Exception as e:
        logger.error(f"获取用户收藏失败: {str(e)}")
        return []

def get_user_ratings(db, user_id: int) -> Dict[int, float]:
    """获取用户对歌曲的加权评分"""
    try:
        # 从user_song_ratings视图获取用户评分
        ratings = db.execute("""
            SELECT song_id, weighted_score
            FROM user_song_ratings
            WHERE consumer_id = :user_id
        """, {"user_id": user_id}).fetchall()
        return {r[0]: float(r[1]) for r in ratings}
    except Exception as e:
        logger.error(f"获取用户评分失败: {str(e)}")
        return {}

def build_user_features(db) -> Dict[int, Dict]:
    """
    构建用户特征序列
    包括以下内容：
        1. 用户播放序列
        2. 用户收藏序列
        3. 用户评分序列
    
    Args:
        db: 数据库会话
        
    Returns:
        Dict[int, Dict]: 用户ID到特征字典的映射，特征数据为原始格式（未序列化）
    """
    try:
        # 获取所有活跃用户（最近30天有播放记录的用户）
        thirty_days_ago = datetime.now() - timedelta(days=30)
        active_users = db.query(PlayHistory.user_id)\
            .filter(PlayHistory.play_time >= thirty_days_ago)\
            .distinct()\
            .all()
            
        logger.info(f"找到 {len(active_users)} 个活跃用户")
        
        user_features = {}
        for user_id, in active_users:
            # 1. 获取用户最近的播放记录
            recent_plays = db.query(PlayHistory.song_id)\
                .filter(PlayHistory.user_id == user_id)\
                .order_by(desc(PlayHistory.play_time))\
                .limit(int(MODEL_CONFIG['sequence_length']*MODEL_CONFIG['playhistory_ratio']))\
                .all()
            play_sequence = [song_id for song_id, in recent_plays][::-1]  # 从旧到新
            
            # 2. 获取用户收藏的歌曲
            favorites = get_user_favorites(db, user_id)
            
            # 3. 获取用户对歌曲的评分
            ratings = get_user_ratings(db, user_id)
            
            # 构建用户特征字典（保持原始数据格式）
            user_features[user_id] = {
                'recent_plays': play_sequence,
                'favorite_songs': favorites,
                'song_ratings': ratings
            }
            
        logger.info(f"成功构建 {len(user_features)} 个用户的特征")
        return user_features
        
    except Exception as e:
        logger.error(f"构建用户特征时发生错误: {str(e)}")
        raise

def update_user_features(db, user_features: Dict[int, Dict]):
    """
    更新用户特征到数据库
    
    Args:
        db: 数据库会话
        user_features: 用户ID到特征字典的映射，特征数据为原始格式
    """
    try:
        for user_id, features in user_features.items():
            # 更新或插入用户特征
            user_feature = db.query(UserFeatures).filter(UserFeatures.user_id == user_id).first()
            if user_feature:
                user_feature.recent_plays = features['recent_plays']
                user_feature.favorite_songs = features['favorite_songs']
                user_feature.song_ratings = features['song_ratings']
                user_feature.update_time = datetime.now()
            else:
                user_feature = UserFeatures(
                    user_id=user_id,
                    recent_plays=features['recent_plays'],
                    favorite_songs=features['favorite_songs'],
                    song_ratings=features['song_ratings'],
                    update_time=datetime.now()
                )
                db.add(user_feature)
                
        db.commit()
        logger.info("用户特征更新完成")
        
    except Exception as e:
        db.rollback()
        logger.error(f"更新用户特征时发生错误: {str(e)}")
        raise

def get_minio_client():
    """获取MinIO客户端实例"""
    return Minio(
        endpoint=MINIO_CONFIG['endpoint'],
        access_key=MINIO_CONFIG['access_key'],
        secret_key=MINIO_CONFIG['secret_key'],
        secure=MINIO_CONFIG['secure']
    )

def check_and_update_embeddings(db):
    """
    检查并更新歌曲的嵌入向量
    1. 检查已删除的歌曲，删除对应的嵌入向量文件
    2. 检查新增的歌曲，生成对应的嵌入向量
    """
    try:
        # 获取所有歌曲的ID和URL映射
        songs = db.query(Song).all()
        song_id_url_map = {song.id: song.url for song in songs}
        
        # 确保嵌入向量目录存在
        if not os.path.exists(AUDIO_EMBEDDINGS_DIR):
            os.makedirs(AUDIO_EMBEDDINGS_DIR)
            
        # 获取现有的嵌入向量文件
        existing_embeddings = set(f.split('.')[0] for f in os.listdir(AUDIO_EMBEDDINGS_DIR) 
                                if f.endswith('.npy'))
        
        # 检查已删除的歌曲
        for embedding_file in existing_embeddings:
            if int(embedding_file) not in song_id_url_map:
                # 删除不存在的歌曲的嵌入向量文件
                os.remove(os.path.join(AUDIO_EMBEDDINGS_DIR, f"{embedding_file}.npy"))
                logger.info(f"已删除不存在的歌曲的嵌入向量文件: {embedding_file}.npy")
        
        # 检查新增的歌曲
        minio_client = get_minio_client()
        
        # 确保音频文件目录存在
        if not os.path.exists(AUDIO_FILES_DIR):
            os.makedirs(AUDIO_FILES_DIR)
            
        for song_id, url in song_id_url_map.items():
            embedding_file = os.path.join(AUDIO_EMBEDDINGS_DIR, f"{song_id}.npy")
            if not os.path.exists(embedding_file):
                try:
                    # 从MinIO下载音频文件
                    # 注意从数据库中得到的songURL的开头是'{/bucket_name/}'+{存储路径}
                    # 如果需要得到存储路径，需要去掉开头的'{/bucket_name/}'
                    # 例如：'/user01/audio/song.mp3' -> 'audio/song.mp3'
                    bucket_name = MINIO_CONFIG['bucket_name']
                    url = url.split(bucket_name)[1]


                    # 得到存储路径
                    audio_file = os.path.join(AUDIO_FILES_DIR, f"{song_id}.mp3")
                    minio_client.fget_object(MINIO_CONFIG['bucket_name'], url, audio_file)

                    # 处理音频文件并生成嵌入向量
                    process_single_audio_file_named_by_song_id(audio_file)

                except Exception as e:
                    logger.error(f"处理歌曲 {song_id} 时发生错误: {str(e)}")
                    continue
                    
    except Exception as e:
        logger.error(f"检查和更新嵌入向量时发生错误: {str(e)}")
        raise

def generate_recommendations():
    """生成推荐"""
    db = next(get_db())
    try:
        # 首先检查并更新嵌入向量
        check_and_update_embeddings(db)
        
        # 构建用户特征
        user_features = build_user_features(db)
        
        # 更新用户特征到数据库
        update_user_features(db, user_features)
        
        # 初始化预测器
        predictor = SASRecPredictor()
        
        # 批量预测
        recommendations = predictor.batch_predict(user_features)
        
        # 更新推荐结果
        for user_id, items in recommendations.items():
            # 检查是否已存在该用户的推荐记录
            existing_recommendation = db.query(UserRecommendations).filter_by(user_id=user_id).first()
            
            if existing_recommendation:
                # 更新现有记录
                existing_recommendation.song_ids = items
            else:
                # 创建新记录
                new_recommendation = UserRecommendations(
                    user_id=user_id,
                    model_version=MODEL_CONFIG['version'],
                    song_ids=items
                )
                db.add(new_recommendation)
                
        # 提交更改
        db.commit()
        logger.info("推荐生成完成")
        
    except Exception as e:
        db.rollback()
        logger.error(f"生成推荐时发生错误: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    generate_recommendations() 