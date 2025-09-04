#!/bin/bash

# Mike Server 启动脚本

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "错误: 虚拟环境不存在，请先创建虚拟环境"
    exit 1
fi

# 激活虚拟环境
source .venv/bin/activate

# 检查依赖
echo "检查Python依赖..."
pip install -r requirements.txt

# 创建必要的目录
mkdir -p logs data/temp data/models

# 初始化数据库
echo "初始化数据库..."
python src/scripts/init_db.py

# 启动应用
echo "启动Mike Server..."
python run.py
