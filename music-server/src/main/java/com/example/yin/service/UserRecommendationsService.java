package com.example.yin.service;
import com.baomidou.mybatisplus.extension.service.IService;
import com.example.yin.model.domain.UserRecommendations;
public interface UserRecommendationsService extends IService<UserRecommendations> {

    /**
     * 获取用户最近一次推荐
     * @param userId 用户ID
     * @return 推荐记录
     */
    UserRecommendations getLatestRecommendations(Long userId);
} 