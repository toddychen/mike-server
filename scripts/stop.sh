#!/bin/bash

# Mike Server 停止脚本

echo "正在停止Mike Server..."

# 查找并停止Python进程
pids=$(ps aux | grep "python.*run.py" | grep -v grep | awk '{print $2}')

if [ -z "$pids" ]; then
    echo "没有找到运行中的Mike Server进程"
else
    for pid in $pids; do
        echo "停止进程 $pid"
        kill $pid
    done
    echo "Mike Server已停止"
fi
