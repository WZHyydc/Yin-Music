package com.example.yin.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.example.yin.model.domain.Banner;

import java.util.List;

/**
* @description 针对表【banner】的数据库操作Service
*/
public interface BannerService extends IService<Banner> {

    List<Banner> getAllBanner();

}
