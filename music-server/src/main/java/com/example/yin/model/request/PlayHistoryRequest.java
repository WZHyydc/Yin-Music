package com.example.yin.model.request;
import lombok.Data;

@Data
public class PlayHistoryRequest {
    private Integer userId;

    private Integer songId;
}
