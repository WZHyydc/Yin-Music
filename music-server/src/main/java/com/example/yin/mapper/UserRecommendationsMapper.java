package com.example.yin.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.example.yin.model.domain.UserRecommendations;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface UserRecommendationsMapper extends BaseMapper<UserRecommendations> {
    /**
     * 查最近一次的推荐
     * @param userId 用户ID
     * @return 推荐记录
     */
    UserRecommendations getLatestRecommendations(@Param("userId") Long userId);
} 