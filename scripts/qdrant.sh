#!/bin/bash

# Qdrant管理脚本

case "$1" in
    start)
        echo "启动Qdrant..."
        docker-compose up -d qdrant
        echo "Qdrant已启动，访问地址: http://localhost:6333"
        ;;
    stop)
        echo "停止Qdrant..."
        docker-compose stop qdrant
        echo "Qdrant已停止"
        ;;
    restart)
        echo "重启Qdrant..."
        docker-compose restart qdrant
        echo "Qdrant已重启"
        ;;
    status)
        echo "Qdrant状态:"
        docker-compose ps qdrant
        ;;
    logs)
        echo "查看Qdrant日志:"
        docker-compose logs -f qdrant
        ;;
    clean)
        echo "清理Qdrant数据..."
        docker-compose down -v
        echo "Qdrant数据已清理"
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|logs|clean}"
        echo ""
        echo "命令说明:"
        echo "  start   - 启动Qdrant"
        echo "  stop    - 停止Qdrant"
        echo "  restart - 重启Qdrant"
        echo "  status  - 查看状态"
        echo "  logs    - 查看日志"
        echo "  clean   - 清理数据"
        exit 1
        ;;
esac
