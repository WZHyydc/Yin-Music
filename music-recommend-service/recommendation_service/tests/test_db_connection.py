import unittest
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, PlayHistory, UserFeatures, UserRecommendations
from config import DB_CONFIG

class TestDatabaseConnection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """测试类初始化，创建数据库连接"""
        # 创建数据库连接
        DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        cls.engine = create_engine(DATABASE_URL)
        cls.Session = sessionmaker(bind=cls.engine)
        
    def setUp(self):
        """每个测试方法前执行，创建新的会话"""
        self.session = self.Session()
        
    def tearDown(self):
        """每个测试方法后执行，关闭会话"""
        self.session.close()
        

    def test_user_features(self):
        """测试用户特征数据"""
        try:
            # 获取所有用户特征
            features = self.session.query(UserFeatures).all()
            print(f"\n找到 {len(features)} 个用户特征")
            
            # 打印前5个用户特征
            for i, feature in enumerate(features[:5]):
                print(f"\n用户 {feature.user_id} 的特征:")
                print(f"  最近播放: {json.loads(feature.recent_plays)}")
                print(f"  收藏歌曲: {json.loads(feature.favorite_songs)}")
                print(f"  歌曲评分: {json.loads(feature.song_ratings)}")
                print(f"  更新时间: {feature.update_time}")
                
            self.assertTrue(True)  # 如果没有异常，测试通过
        except Exception as e:
            self.fail(f"获取用户特征失败: {str(e)}")
            
    def test_recent_play_history(self):
        """测试最近播放记录"""
        try:
            # 获取最近7天的播放记录
            seven_days_ago = datetime.now() - timedelta(days=7)
            recent_plays = self.session.query(PlayHistory)\
                .filter(PlayHistory.play_time >= seven_days_ago)\
                .order_by(PlayHistory.play_time.desc())\
                .limit(10)\
                .all()
                
            print(f"\n最近7天的播放记录（前10条）:")
            for play in recent_plays:
                print(f"用户 {play.user_id} 在 {play.play_time} 播放了歌曲 {play.song_id}")
                
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"获取播放记录失败: {str(e)}")

if __name__ == '__main__':
    unittest.main() 