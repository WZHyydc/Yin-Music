-- MySQL dump 10.13  Distrib 5.7.21, for macos10.13 (x86_64)
--
-- Host: localhost    Database: tp_music
-- ------------------------------------------------------
-- Server version	5.7.21

create database if not exists tp_music;
use tp_music;
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admin`
--

DROP TABLE IF EXISTS `admin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;3
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `admin` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(45) NOT NULL,
  `password` varchar(45) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `name_UNIQUE` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `admin`
--

LOCK TABLES `admin` WRITE;
/*!40000 ALTER TABLE `admin` DISABLE KEYS */;
/*!40000 ALTER TABLE `admin` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `banner`
--

DROP TABLE IF EXISTS `banner`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `banner` (
  `id` int(10) NOT NULL AUTO_INCREMENT,
  `pic` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `banner`
--

LOCK TABLES `banner` WRITE;
/*!40000 ALTER TABLE `banner` DISABLE KEYS */;
/*!40000 ALTER TABLE `banner` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `collect`
--

DROP TABLE IF EXISTS `collect`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `collect` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned NOT NULL,
  `type` tinyint(4) NOT NULL, -- 0:歌曲 1:歌单
  `song_id` int(10) unsigned DEFAULT NULL,
  `song_list_id` int(10) unsigned DEFAULT NULL,
  `create_time` datetime NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=101 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `collect`
--

LOCK TABLES `collect` WRITE;
/*!40000 ALTER TABLE `collect` DISABLE KEYS */;

UNLOCK TABLES;

--
-- Table structure for table `comment`
--

DROP TABLE IF EXISTS `comment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `comment` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `user_id` int(10) unsigned NOT NULL,
  `song_id` int(10) unsigned DEFAULT NULL,
  `song_list_id` int(10) unsigned DEFAULT NULL,
  `content` varchar(255) DEFAULT NULL,
  `create_time` datetime DEFAULT NULL,
  `type` tinyint(4) NOT NULL,
  `up` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=73 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comment`
--

LOCK TABLES `comment` WRITE;
/*!40000 ALTER TABLE `comment` DISABLE KEYS */;

/*!40000 ALTER TABLE `comment` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `consumer`
--

DROP TABLE IF EXISTS `consumer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `consumer` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `username` varchar(255) NOT NULL,
  `password` varchar(100) NOT NULL,
  `sex` tinyint(4) DEFAULT NULL,
  `phone_num` char(15) DEFAULT NULL,
  `email` char(30) DEFAULT NULL,
  `birth` datetime DEFAULT NULL,
  `introduction` varchar(255) DEFAULT NULL,
  `location` varchar(45) DEFAULT NULL,
  `avator` varchar(255) DEFAULT NULL,
  `create_time` datetime NOT NULL,
  `update_time` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username_UNIQUE` (`username`),
  UNIQUE KEY `phone_num_UNIQUE` (`phone_num`),
  UNIQUE KEY `email_UNIQUE` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=63 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `consumer`
--

LOCK TABLES `consumer` WRITE;
/*!40000 ALTER TABLE `consumer` DISABLE KEYS */;

/*!40000 ALTER TABLE `consumer` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `list_song`
--

DROP TABLE IF EXISTS `list_song`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `list_song` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `song_id` int(10) unsigned NOT NULL,
  `song_list_id` int(10) unsigned NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=210 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `list_song`
--

LOCK TABLES `list_song` WRITE;
/*!40000 ALTER TABLE `list_song` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `rank_list`
--

DROP TABLE IF EXISTS `rank_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rank_list` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT,
  `song_list_id` bigint(20) unsigned NOT NULL,
  `consumer_id` bigint(20) unsigned NOT NULL,
  `score` int(10) unsigned NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `consumerId` (`consumer_id`,`song_list_id`)
) ENGINE=InnoDB AUTO_INCREMENT=66 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rank_list`
--

LOCK TABLES `rank_list` WRITE;
/*!40000 ALTER TABLE `rank_list` DISABLE KEYS */;
/*!40000 ALTER TABLE `rank_list` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `singer`
--

DROP TABLE IF EXISTS `singer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `singer` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(45) NOT NULL,
  `sex` tinyint(4) DEFAULT NULL,
  `pic` varchar(255) DEFAULT NULL,
  `birth` datetime DEFAULT NULL,
  `location` varchar(45) DEFAULT NULL,
  `introduction` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=47 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `singer`
--



--
-- Table structure for table `song`
--

DROP TABLE IF EXISTS `song`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `song` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `singer_id` int(10) unsigned NOT NULL,
  `name` varchar(45) NOT NULL,
  `introduction` varchar(255) DEFAULT NULL,
  `create_time` datetime NOT NULL COMMENT '发行时间',
  `update_time` datetime NOT NULL,
  `pic` varchar(255) DEFAULT NULL,
  `lyric` text,
  `url` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=119 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `song`
--


--
-- Table structure for table `song_list`
--

DROP TABLE IF EXISTS `song_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `song_list` (
  `id` int(10) unsigned NOT NULL AUTO_INCREMENT,
  `title` varchar(255) NOT NULL,
  `pic` varchar(255) DEFAULT NULL,
  `introduction` text,
  `style` varchar(10) DEFAULT '无',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=87 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `song_list`
--
-- Table structure for table `user_support`
--

DROP TABLE IF EXISTS `user_support`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_support` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `comment_id` int(11) NOT NULL,
  `user_id` varchar(45) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_support`
--

LOCK TABLES `user_support` WRITE;
/*!40000 ALTER TABLE `user_support` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_support` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;



# 创建触发器，当consumer删除数据（用户）时，删除comment相关的数据（根据用户user_id), 删除rank_list相关的数据（根据consumer_id), 删usersupport相关的数据（根据user_id)
DELIMITER $$
DROP TRIGGER IF EXISTS `delete_consumer`$$
CREATE TRIGGER `delete_consumer` AFTER DELETE ON `consumer` FOR EACH ROW
BEGIN
    DELETE FROM comment WHERE user_id = OLD.id;
END$$

DELIMITER $$
DROP TRIGGER IF EXISTS `delete_rank_list`$$
CREATE TRIGGER `delete_rank_list` AFTER DELETE ON `consumer` FOR EACH ROW
BEGIN
    DELETE FROM rank_list WHERE consumer_id = OLD.id;
END$$

DELIMITER $$
DROP TRIGGER IF EXISTS `delete_user_support`$$
CREATE TRIGGER `delete_user_support` AFTER DELETE ON `consumer` FOR EACH ROW
BEGIN
    DELETE FROM user_support WHERE user_id = OLD.id;
END$$


#song表下url字段
#在所有url字段前加上/user01
update song set url = concat('/user01',url);
#在所有pic字段前加上/user01
update song set pic = concat('/user01',pic);

#consumer表下avtor字段
#在所有avtor字段前加上/user01
update consumer set avator = concat('/user01',avator);

#singer表下pic字段
#在所有pic字段前加上/user01
update singer set pic = concat('/user01',pic);

#song_list表下pic字段
#在所有pic字段前加上/user01
update song_list set pic = concat('/user01',pic);

#banner表下pic字段
#在所有pic字段前加上/user01
update banner set pic = concat('/user01',pic);


DROP TABLE IF EXISTS `play_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `play_history` (
  `id`         BIGINT       UNSIGNED NOT NULL AUTO_INCREMENT,
  `user_id`    BIGINT       UNSIGNED NOT NULL COMMENT '用户 ID',
  `song_id`    BIGINT       UNSIGNED NOT NULL COMMENT '歌曲 ID',
  `play_time`  DATETIME               NOT NULL
                                DEFAULT CURRENT_TIMESTAMP
                                COMMENT '播放时间',
  PRIMARY KEY (`id`),
  INDEX `idx_user_playtime` (`user_id`, `play_time`)
) ENGINE=InnoDB
  DEFAULT CHARSET=utf8mb4
  COMMENT='记录用户播放历史：user_id, song_id, play_time';


CREATE TABLE `user_recommendations` (
  `user_id`          BIGINT       NOT NULL COMMENT '用户 ID, 外键关联 users 表', 
  `recommend_time`   DATETIME     NOT NULL 
                           DEFAULT CURRENT_TIMESTAMP 
                           COMMENT '推荐生成时间', 
  `model_version`    VARCHAR(64)  NOT NULL COMMENT '推荐模型版本或名称', 
  `song_ids`         JSON         NOT NULL COMMENT 'Top-10 推荐歌曲 ID 列表, JSON 数组',
  PRIMARY KEY (`user_id`, `recommend_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
  COMMENT='用户推荐结果表——用 JSON 存储 10 首歌曲 ID';

/*
    如果视图存在则删除
    创建视图用来计算用户对于歌曲的加权评分
 */
DROP VIEW IF EXISTS user_song_ratings;
CREATE VIEW user_song_ratings AS
SELECT
    r.consumer_id,                      -- 用户ID
    ls.song_id,                          -- 歌曲ID
    SUM(r.score / song_count) AS weighted_score  -- 加权评分
FROM
    rank_list r
JOIN
    list_song ls ON r.song_list_id = ls.song_list_id  -- 关联rank_list和list_song表
JOIN
    (
        SELECT song_list_id, COUNT(*) AS song_count  -- 统计每个歌单中的歌曲数量
        FROM list_song
        GROUP BY song_list_id
    ) song_list_count ON ls.song_list_id = song_list_count.song_list_id
GROUP BY
    r.consumer_id, ls.song_id;


DROP TABLE IF EXISTS `user_features`;
CREATE TABLE `user_features` (
    `user_id`           BIGINT       NOT NULL COMMENT '用户 ID',
    `recent_plays`      JSON         NOT NULL COMMENT '最近播放的100首歌曲ID列表',
    `favorite_songs`    JSON         NOT NULL COMMENT '用户收藏的歌曲ID列表',
    `song_ratings`      JSON         NOT NULL COMMENT '用户对歌曲的加权评分',
    `update_time`       DATETIME     NOT NULL 
                              DEFAULT CURRENT_TIMESTAMP 
                              ON UPDATE CURRENT_TIMESTAMP
                              COMMENT '特征更新时间',
    PRIMARY KEY (`user_id`)
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4
  COMMENT='用户特征表 - 存储用户的播放历史、收藏和评分等特征';
