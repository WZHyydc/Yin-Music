package com.example.yin.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.yin.mapper.UserRecommendationsMapper;
import com.example.yin.model.domain.UserRecommendations;
import com.example.yin.service.UserRecommendationsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class UserRecommendationsServiceImpl extends ServiceImpl<UserRecommendationsMapper, UserRecommendations> implements UserRecommendationsService {

    @Autowired
    private UserRecommendationsMapper userRecommendationsMapper;

    @Override
    public UserRecommendations getLatestRecommendations(Long userId) {
        return userRecommendationsMapper.getLatestRecommendations(userId);
    }
} 