package com.example.yin.controller;

import com.example.yin.common.R;
import com.example.yin.model.request.PlayHistoryRequest;
import com.example.yin.service.PlayHistoryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
public class PlayHistoryController {

    @Autowired
    private PlayHistoryService playHistoryService;

    // 添加播放记录
    @PostMapping("/playhistory/add")
    public R addPlayHistory(@RequestBody PlayHistoryRequest playHistoryRequest) {
        return playHistoryService.addPlayHistory(playHistoryRequest);
    }

    // 获取用户的播放记录
    @GetMapping("/playhistory/de/{userId}")
    public R getPlayHistoryByUserId(@PathVariable Long userId) {
        return playHistoryService.getPlayHistoryByUserId(userId);
    }

    // 删除用户的播放记录
    @DeleteMapping("/playhistory/user/{userId}")
    public R deletePlayHistoryByUserId(@PathVariable Long userId) {
        return playHistoryService.deletePlayHistoryByUserId(userId);
    }
}
