#!/bin/bash

# Mike Server 部署脚本

echo "开始部署Mike Server..."

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装"
    exit 1
fi

# 创建必要的目录
mkdir -p logs data/temp data/models

# 复制环境变量文件
if [ ! -f .env ]; then
    echo "创建环境变量文件..."
    cp env.example .env
    echo "请编辑 .env 文件配置必要的参数"
fi

# 构建并启动服务
echo "构建并启动Docker服务..."
cd docker
docker-compose up -d --build

echo "部署完成！"
echo "服务地址: http://localhost:3000"
echo "API文档: http://localhost:3000/docs"
echo "Qdrant管理界面: http://localhost:6333"
