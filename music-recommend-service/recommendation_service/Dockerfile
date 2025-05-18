# 使用官方的Python 3.8镜像作为基础镜像
FROM python:3.8-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY . /app/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV PYTHONPATH=/app

# 运行调度器
CMD ["python", "scheduler.py"] 