package com.example.yin.service;
import com.baomidou.mybatisplus.extension.service.IService;
import com.example.yin.common.R;
import com.example.yin.model.domain.PlayHistory;
import com.example.yin.model.request.PlayHistoryRequest;

public interface PlayHistoryService extends IService<PlayHistory> {
    R addPlayHistory(PlayHistoryRequest playHistoryRequest);

    R getPlayHistoryByUserId(Long userId);

    R deletePlayHistoryByUserId(Long userId);
}
