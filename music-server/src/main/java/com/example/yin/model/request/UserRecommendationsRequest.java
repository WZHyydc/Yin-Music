package com.example.yin.model.request;

import lombok.Data;

@Data
public class UserRecommendationsRequest {
    private Long userId;
    private String modelVersion;

    private String songIds; // JSON格式的歌曲ID列表

    private String recommendTime; // 推荐时间
}
