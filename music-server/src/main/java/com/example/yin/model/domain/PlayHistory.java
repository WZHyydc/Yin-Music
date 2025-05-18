package com.example.yin.model.domain;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import org.apache.commons.lang3.builder.ToStringBuilder;

import java.io.Serializable;
import java.util.Date;

@TableName(value = "play_history")
@Data
public class PlayHistory implements Serializable {

    @TableId(type = IdType.AUTO)
    private Integer id;

    private Integer songId;

    private Integer userId;

    private Date playTime;

    @Override
    public String toString() {
        return ToStringBuilder.reflectionToString(this);
    }
}
