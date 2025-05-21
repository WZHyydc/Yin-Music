# 音乐推荐微服务

基于SASRec模型的音乐推荐系统微服务实现。

## 功能特点

- 基于用户历史播放序列的个性化推荐
- 使用SASRec（Self-Attentive Sequential Recommendation）模型
- 定时任务自动更新推荐结果
- 支持Docker容器化部署

## 项目结构

```
recommendation_service/
├── config.py              # 配置文件
├── models.py              # 数据库模型
├── run_recommendation.py  # 主推荐脚本
├── scheduler.py           # 定时任务调度器
├── requirements.txt       # 项目依赖
├── Dockerfile            # Docker构建文件
├── tests/                # 测试目录
│   └── test_db_connection.py  # 数据库连接测试
└── sasrec/               # SASRec模型相关
    ├── data/            # 数据目录
    ├── model/           # 模型定义
    │   └── predictor.py # 预测接口
    └── saved/           # 模型保存目录
```

## 环境要求

- Python 3.8+
- MySQL 5.7+
- PyTorch 2.0+

## 安装步骤

1. 克隆项目
```bash
git clone [项目地址]
cd recommendation_service
```

2. 创建虚拟环境
```bash
conda create -n music-recommend python=3.8
conda activate music-recommend
```

3. 安装依赖
```bash
# 安装基础包
conda install pytorch numpy pandas scikit-learn

# 安装其他依赖
pip install -r requirements.txt
```

4. 配置环境变量
创建 `.env` 文件：
```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=music_recommend
```

## 数据库设置

### 1. 创建数据库
```sql
CREATE DATABASE music_recommend CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 创建数据表

#### 用户播放历史表
```sql
CREATE TABLE play_history (
    id           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id      BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    song_id      BIGINT UNSIGNED NOT NULL COMMENT '歌曲ID',
    play_time    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '播放时间',
    PRIMARY KEY (id),
    INDEX idx_user_playtime (user_id, play_time)
) ENGINE=InnoDB CHARSET=utf8mb4 COMMENT='记录用户播放历史';
```

#### 用户特征表
```sql
CREATE TABLE user_features (
    user_id           BIGINT       NOT NULL COMMENT '用户ID',
    recent_plays      JSON         NOT NULL COMMENT '最近播放的100首歌曲ID列表',
    favorite_songs    JSON         NOT NULL COMMENT '用户收藏的歌曲ID列表',
    song_ratings      JSON         NOT NULL COMMENT '用户对歌曲的加权评分',
    update_time       DATETIME     NOT NULL 
                              DEFAULT CURRENT_TIMESTAMP 
                              ON UPDATE CURRENT_TIMESTAMP
                              COMMENT '特征更新时间',
    PRIMARY KEY (user_id)
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4
  COMMENT='用户特征表 - 存储用户的播放历史、收藏和评分等特征';
```

#### 用户推荐结果表
```sql
CREATE TABLE user_recommendations (
    user_id        BIGINT      NOT NULL COMMENT '用户ID',
    recommend_time DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '推荐时间',
    model_version  VARCHAR(64) NOT NULL COMMENT '模型版本',
    song_ids       JSON        NOT NULL COMMENT 'Top-10推荐歌曲ID列表',
    PRIMARY KEY (user_id, recommend_time)
) ENGINE=InnoDB CHARSET=utf8mb4 COMMENT='用户推荐结果';
```

#### 用户收藏表
```sql
CREATE TABLE collect (
    id            INT(10) UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id       INT(10) UNSIGNED NOT NULL COMMENT '用户ID',
    type          TINYINT(4)      NOT NULL COMMENT '0:歌曲 1:歌单',
    song_id       INT(10) UNSIGNED DEFAULT NULL COMMENT '歌曲ID',
    song_list_id  INT(10) UNSIGNED DEFAULT NULL COMMENT '歌单ID',
    create_time   DATETIME        NOT NULL COMMENT '收藏时间',
    PRIMARY KEY (id)
) ENGINE=InnoDB AUTO_INCREMENT=101 CHARSET=utf8 COMMENT='用户收藏记录';
```

#### 用户评分视图
```sql
CREATE VIEW user_song_ratings AS
SELECT
    r.consumer_id   AS user_id,
    ls.song_id,
    SUM(r.score / song_count) AS weighted_score
FROM rank_list r
JOIN list_song ls ON r.song_list_id = ls.song_list_id
JOIN (
    SELECT song_list_id, COUNT(*) AS song_count
    FROM list_song
    GROUP BY song_list_id
) song_list_count ON ls.song_list_id = song_list_count.song_list_id
GROUP BY r.consumer_id, ls.song_id;
```

### 3. 初始化表结构
```bash
python -c "from models import create_tables; create_tables()"
```

## 运行测试

运行数据库连接测试：
```bash
python -m unittest tests/test_db_connection.py
```

测试内容包括：
- 数据库连接测试
- 表存在性检查
- 用户特征数据验证（包括最近播放、收藏和评分）
- 最近播放记录查询

## 使用方法

1. 启动推荐服务
```bash
python scheduler.py
```

2. 手动生成推荐
```bash
python run_recommendation.py
```

## Docker部署

1. 构建镜像
```bash
docker build -t music-recommend-service .
```

2. 运行容器
```bash
docker run -d \
  --name music-recommend \
  -e MYSQL_HOST=host.docker.internal \
  -e MYSQL_PORT=3306 \
  -e MYSQL_USER=your_username \
  -e MYSQL_PASSWORD=your_password \
  -e MYSQL_DATABASE=music_recommend \
  music-recommend-service
```

## 配置说明

主要配置项在 `config.py` 中：

- 数据库配置
- 模型参数
- 推荐参数

## 注意事项

1. 确保MySQL服务已启动
2. 确保模型文件 `sasrec/saved/best_model.pt` 存在
3. 定期备份数据库
4. 监控系统资源使用情况

## 问题排查

如果遇到问题，请检查：

1. 数据库连接是否正常
2. 环境变量是否正确设置
3. 依赖包是否完整安装
4. 日志文件中的错误信息