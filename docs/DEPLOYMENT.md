# Mike Server 部署文档

## 系统要求

- Python 3.11+
- 内存: 至少4GB RAM
- 存储: 至少2GB可用空间
- 网络: 可访问互联网（用于下载模型）

## 部署方式

### 方式1: 传统Python部署

#### 1. 克隆项目
```bash
git clone <repository-url>
cd mike-server
```

#### 2. 创建虚拟环境
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate  # Windows
```

#### 3. 安装依赖
```bash
pip install -r requirements.txt
```

#### 4. 配置环境变量
```bash
cp env.example .env
# 编辑 .env 文件配置必要参数
```

#### 5. 启动Qdrant服务
```bash
# 使用Docker启动Qdrant
docker run -d -p 6333:6333 qdrant/qdrant:latest

# 或使用Docker Compose
cd docker
docker-compose up -d qdrant
```

#### 6. 初始化数据库
```bash
python src/scripts/init_db.py
```

#### 7. 启动服务
```bash
# 使用启动脚本
./scripts/start.sh

# 或直接启动
python run.py
```

### 方式2: Docker部署

#### 1. 使用Docker Compose（推荐）
```bash
cd docker
docker-compose up -d --build
```

#### 2. 手动构建Docker镜像
```bash
cd docker
docker build -t mike-server .
docker run -d -p 3000:3000 mike-server
```

## 环境变量配置

### 必需配置
```bash
# 管理员密钥
ADMIN_SECRET=heymike

# 向量数据库
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 可选配置
```bash
# 服务器配置
PORT=3000
HOST=0.0.0.0

# Whisper模型
WHISPER_MODEL=tiny

# 调度器配置
AUTO_START_SCHEDULER=true
NEWS_FETCH_INTERVAL_HOURS=1

# 新闻API配置
NEWS_API_BASE_URL=https://your-news-api.com
NEWS_API_KEY=your_api_key
```

## 服务管理

### 启动服务
```bash
./scripts/start.sh
```

### 停止服务
```bash
./scripts/stop.sh
```

### 重启服务
```bash
./scripts/restart.sh
```

### 查看日志
```bash
tail -f logs/app.log
tail -f logs/scheduler.log
```

## 独立调度器

如果需要单独运行新闻调度器：

```bash
python src/scripts/run_scheduler.py
```

## 系统信号控制

```bash
# 启动调度器
kill -USR1 <process_id>

# 停止调度器
kill -USR2 <process_id>

# 优雅关闭
kill -TERM <process_id>
```

## 监控和健康检查

### 健康检查端点
- 应用健康: `GET /health`
- 向量数据库: `GET /api/news/health`
- 调度器状态: `GET /api/admin/scheduler/status?secret=heymike`

### 日志监控
```bash
# 实时监控应用日志
tail -f logs/app.log | grep ERROR

# 监控调度器日志
tail -f logs/scheduler.log | grep "新闻抓取任务"
```

## 故障排除

### 常见问题

#### 1. Qdrant连接失败
```bash
# 检查Qdrant服务状态
docker ps | grep qdrant

# 检查端口是否开放
netstat -an | grep 6333
```

#### 2. 模型下载失败
```bash
# 手动下载Whisper模型
python -c "import whisper; whisper.load_model('tiny')"
```

#### 3. 内存不足
```bash
# 检查内存使用
free -h

# 使用更小的Whisper模型
export WHISPER_MODEL=tiny
```

#### 4. 权限问题
```bash
# 设置脚本执行权限
chmod +x scripts/*.sh src/scripts/*.py
```

## 性能优化

### 1. Whisper模型选择
- `tiny`: 最快，准确度较低
- `base`: 平衡速度和准确度
- `small`: 较好准确度
- `medium`: 高准确度
- `large`: 最高准确度，最慢

### 2. 向量数据库优化
```bash
# 调整Qdrant配置
export QDRANT_HOST=localhost
export QDRANT_PORT=6333
```

### 3. 调度器优化
```bash
# 调整抓取间隔
export NEWS_FETCH_INTERVAL_HOURS=2

# 调整并发数
export MAX_CONCURRENT_SCRAPES=3
```

## 备份和恢复

### 备份数据
```bash
# 备份Qdrant数据
docker exec qdrant tar -czf /tmp/qdrant_backup.tar.gz /qdrant/storage
docker cp qdrant:/tmp/qdrant_backup.tar.gz ./qdrant_backup.tar.gz
```

### 恢复数据
```bash
# 恢复Qdrant数据
docker cp qdrant_backup.tar.gz qdrant:/tmp/
docker exec qdrant tar -xzf /tmp/qdrant_backup.tar.gz -C /
```

## 安全建议

1. 修改默认的`ADMIN_SECRET`
2. 使用HTTPS（生产环境）
3. 限制管理API的访问IP
4. 定期更新依赖包
5. 监控异常访问日志
