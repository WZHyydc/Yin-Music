package com.example.yin.controller;

import com.example.yin.model.domain.UserRecommendations;
import com.example.yin.service.UserRecommendationsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/song")
public class RecommendController {

    @Autowired
    private UserRecommendationsService userRecommendationsService;

    @GetMapping("/recommend")
    public String getRecommendPlayList(@RequestParam Long userId) {
        UserRecommendations recommendations = userRecommendationsService.getLatestRecommendations(userId);
        return recommendations != null ? recommendations.getSongIds() : "[]";
    }
} 