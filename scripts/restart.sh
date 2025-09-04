#!/bin/bash

# Mike Server 重启脚本

echo "正在重启Mike Server..."

# 先停止
./scripts/stop.sh

# 等待进程完全停止
sleep 2

# 再启动
./scripts/start.sh
