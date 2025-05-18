package com.example.yin.model.domain;

import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.util.Date;

@Data
@TableName("user_recommendations")
public class UserRecommendations {
    private Long userId;
    private Date recommendTime;
    private String modelVersion;
    private String songIds; // 存储JSON格式的歌曲ID列表
} 