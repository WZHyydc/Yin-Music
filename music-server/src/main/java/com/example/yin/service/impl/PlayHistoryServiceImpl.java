package com.example.yin.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.example.yin.common.R;
import com.example.yin.mapper.PlayHistoryMapper;
import com.example.yin.model.domain.PlayHistory;
import com.example.yin.model.request.PlayHistoryRequest;
import com.example.yin.service.PlayHistoryService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;


@Service
public class PlayHistoryServiceImpl extends ServiceImpl<PlayHistoryMapper, PlayHistory> implements PlayHistoryService {

    @Autowired
    private PlayHistoryMapper playHistoryMapper;

    @Override
    public R addPlayHistory(PlayHistoryRequest playHistoryRequest) {
        PlayHistory playHistory = new PlayHistory();
        BeanUtils.copyProperties(playHistoryRequest, playHistory);
        if (playHistoryMapper.insert(playHistory) > 0) {
            return R.success("添加播放记录成功");
        } else {
            return R.error("添加播放记录失败");
        }
    }

    @Override
    public R getPlayHistoryByUserId(Long userId) {
        QueryWrapper<PlayHistory> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId);
        return R.success(null, playHistoryMapper.selectList(queryWrapper));
    }

    @Override
    public R deletePlayHistoryByUserId(Long userId) {
        QueryWrapper<PlayHistory> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", userId);
        if (playHistoryMapper.delete(queryWrapper) > 0) {
            return R.success("删除播放记录成功");
        } else {
            return R.error("删除播放记录失败");
        }
    }
}
