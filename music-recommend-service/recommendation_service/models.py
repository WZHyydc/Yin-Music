from sqlalchemy import create_engine, Column, Integer, BigInteger, DateTime, JSON, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DB_CONFIG

# 创建数据库连接
DATABASE_URL = f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class PlayHistory(Base):
    __tablename__ = 'play_history'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False, comment='用户ID')
    song_id = Column(BigInteger, nullable=False, comment='歌曲ID')
    play_time = Column(DateTime, nullable=False, server_default='CURRENT_TIMESTAMP', comment='播放时间')

class UserFeatures(Base):
    __tablename__ = 'user_features'
    
    user_id = Column(BigInteger, primary_key=True, comment='用户ID')
    recent_plays = Column(JSON, nullable=False, comment='最近播放的100首歌曲ID列表')
    favorite_songs = Column(JSON, nullable=False, comment='用户收藏的歌曲ID列表')
    song_ratings = Column(JSON, nullable=False, comment='用户对歌曲的加权评分')
    update_time = Column(DateTime, nullable=False, 
                        server_default='CURRENT_TIMESTAMP',
                        onupdate='CURRENT_TIMESTAMP',
                        comment='特征更新时间')

class UserRecommendations(Base):
    __tablename__ = 'user_recommendations'
    
    user_id = Column(BigInteger, primary_key=True, comment='用户ID')
    recommend_time = Column(DateTime, primary_key=True, server_default='CURRENT_TIMESTAMP', comment='推荐时间')
    model_version = Column(String(64), nullable=False, comment='模型版本')
    song_ids = Column(JSON, nullable=False, comment='Top-10推荐歌曲ID列表')

class Song(Base):
    __tablename__ = 'song'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    singer_id = Column(Integer, nullable=False)
    name = Column(String(45), nullable=False)
    update_time = Column(DateTime, nullable=False)
    url = Column(String(255), nullable=False)

# 创建所有表
def create_tables():
    Base.metadata.create_all(bind=engine)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 