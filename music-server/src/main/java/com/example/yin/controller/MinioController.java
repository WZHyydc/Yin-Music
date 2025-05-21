package com.example.yin.controller;

import io.minio.GetObjectArgs;
import io.minio.MinioClient;
import org.apache.commons.io.IOUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import java.io.InputStream;


@Controller
public class MinioController {
    @Value("${minio.bucket-name}")
    private String bucketName;
    @Autowired
    private MinioClient minioClient;
    //获取默认图片
    @GetMapping("/img/default/{fileName:.+}")
    public ResponseEntity<byte[]> getDefaultAdminImage(@PathVariable String fileName) throws Exception {
        InputStream stream = minioClient.getObject(
                GetObjectArgs.builder()
                        .bucket(bucketName)
                        .object("/img/default/"+fileName)
                        .build()
        );

        byte[] bytes = IOUtils.toByteArray(stream);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.IMAGE_JPEG); // 设置响应内容类型为图片类型

        return new ResponseEntity<>(bytes, headers, HttpStatus.OK);
    }
    //获取默认头像
    @GetMapping("/${minio.bucket-name}/img/default/{fileName:.+}")
    public ResponseEntity<byte[]> getDefaultImage(@PathVariable String fileName) throws Exception {
        InputStream stream = minioClient.getObject(
                GetObjectArgs.builder()
                        .bucket(bucketName)
                        .object("/img/default/"+fileName)
                        .build()
        );

        byte[] bytes = IOUtils.toByteArray(stream);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.IMAGE_JPEG); // 设置响应内容类型为图片类型

        return new ResponseEntity<>(bytes, headers, HttpStatus.OK);
    }
    //获取歌曲
    @GetMapping("/${minio.bucket-name}/song/{fileName:.+}")
    public ResponseEntity<byte[]> getMusic(@PathVariable String fileName) {
        try {
            GetObjectArgs args = GetObjectArgs.builder()
                    .bucket(bucketName)
                    .object("/song/"+fileName)
                    .build();
            InputStream inputStream = minioClient.getObject(args);

            // 将文件内容读取为字节数组
            byte[] bytes = IOUtils.toByteArray(inputStream);

            // 设置响应头，指示浏览器如何处理响应内容
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_OCTET_STREAM);
            headers.setContentDispositionFormData("attachment", fileName); // 如果需要下载文件，可以使用此头部

            // 返回字节数组作为响应
            return new ResponseEntity<>(bytes, headers, HttpStatus.OK);
        } catch (Exception e) {
            e.printStackTrace();
            return new ResponseEntity<>(HttpStatus.INTERNAL_SERVER_ERROR);
        }
    }
    //获取歌手图片
    @GetMapping("/${minio.bucket-name}/img/singerPic/{fileName:.+}")
    public ResponseEntity<byte[]> getImage(@PathVariable String fileName) throws Exception {
        InputStream stream = minioClient.getObject(
                GetObjectArgs.builder()
                        .bucket(bucketName)
                        .object("/img/singerPic/"+fileName)
                        .build()
        );

        byte[] bytes = IOUtils.toByteArray(stream);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.IMAGE_JPEG); // 设置响应内容类型为图片类型，根据实际情况修改

        return new ResponseEntity<>(bytes, headers, HttpStatus.OK);
    }
    //获取歌单图片
    @GetMapping("/${minio.bucket-name}/img/songListPic/{fileName:.+}")
    public ResponseEntity<byte[]> getImage1(@PathVariable String fileName) throws Exception {
        InputStream stream = minioClient.getObject(
                GetObjectArgs.builder()
                        .bucket(bucketName)
                        .object("/img/songListPic/"+fileName)
                        .build()
        );

        byte[] bytes = IOUtils.toByteArray(stream);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.IMAGE_JPEG); // 设置响应内容类型为图片类型，根据实际情况修改

        return new ResponseEntity<>(bytes, headers, HttpStatus.OK);
    }
    //获取歌的图片
    @GetMapping("/${minio.bucket-name}/img/songPic/{fileName:.+}")
    public ResponseEntity<byte[]> getImage2(@PathVariable String fileName) throws Exception {
        InputStream stream = minioClient.getObject(
                GetObjectArgs.builder()
                        .bucket(bucketName)
                        .object("/img/songPic/"+fileName)
                        .build()
        );

        byte[] bytes = IOUtils.toByteArray(stream);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.IMAGE_JPEG); // 设置响应内容类型为图片类型，根据实际情况修改

        return new ResponseEntity<>(bytes, headers, HttpStatus.OK);
    }
    //获取头像
    @GetMapping("/${minio.bucket-name}/img/avatorImages/{fileName:.+}")
    public ResponseEntity<byte[]> getImage3(@PathVariable String fileName) throws Exception {
        InputStream stream = minioClient.getObject(
                GetObjectArgs.builder()
                        .bucket(bucketName)
                        .object("/img/avatorImages/"+fileName)
                        .build()
        );

        byte[] bytes = IOUtils.toByteArray(stream);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.IMAGE_JPEG); // 设置响应内容类型为图片类型，根据实际情况修改

        return new ResponseEntity<>(bytes, headers, HttpStatus.OK);
    }

    //获取轮播图
    @GetMapping("/${minio.bucket-name}/img/swiper/{fileName:.+}")
    public ResponseEntity<byte[]> getImage4(@PathVariable String fileName) throws Exception {
        InputStream stream = minioClient.getObject(
                GetObjectArgs.builder()
                        .bucket(bucketName)
                        .object("/img/swiper/"+fileName)
                        .build()
        );

        byte[] bytes = IOUtils.toByteArray(stream);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.IMAGE_JPEG); // 设置响应内容类型为图片类型，根据实际情况修改

        return new ResponseEntity<>(bytes, headers, HttpStatus.OK);
    }

}
