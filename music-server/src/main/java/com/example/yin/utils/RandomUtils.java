package com.example.yin.utils;

import java.security.SecureRandom;

public class RandomUtils {
    private static final SecureRandom secureRandom = new SecureRandom();
    private static final String NUMBERS = "0123456789";
    private static final String UPPER_CASE = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
    private static final String LOWER_CASE = "abcdefghijklmnopqrstuvwxyz";
    
    public static String code() {
        StringBuilder code = new StringBuilder();
        
        // 确保至少包含一个数字
        code.append(NUMBERS.charAt(secureRandom.nextInt(NUMBERS.length())));
        
        // 确保至少包含一个大写字母
        code.append(UPPER_CASE.charAt(secureRandom.nextInt(UPPER_CASE.length())));
        
        // 确保至少包含一个小写字母
        code.append(LOWER_CASE.charAt(secureRandom.nextInt(LOWER_CASE.length())));
        
        // 生成剩余的随机字符
        String allChars = NUMBERS + UPPER_CASE + LOWER_CASE;
        for (int i = 0; i < 2; i++) {
            code.append(allChars.charAt(secureRandom.nextInt(allChars.length())));
        }
        
        // 打乱字符顺序
        char[] codeArray = code.toString().toCharArray();
        for (int i = codeArray.length - 1; i > 0; i--) {
            int j = secureRandom.nextInt(i + 1);
            char temp = codeArray[i];
            codeArray[i] = codeArray[j];
            codeArray[j] = temp;
        }
        
        return new String(codeArray);
    }
}
