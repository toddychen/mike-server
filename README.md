# Mike Server

一个集成了音频转文字和新闻搜索功能的Web服务，使用本地Whisper模型和向量数据库。

## 功能特性

### 🎵 音频转文字
- 支持多种音频格式（MP3, MP4, M4A, WAV等）
- 使用本地Whisper模型，无需网络连接
- 支持多语言识别
- 可配置的模型大小（tiny到large）

### 📰 新闻搜索
- 自动抓取新闻内容
- 向量化存储和语义搜索
- 支持时间范围过滤
- 去重和内容质量验证

### ⚙️ 任务调度
- 自动新闻抓取和存储
- 可配置的抓取间隔
- 支持手动触发和控制
- 完善的日志记录

## 技术架构

- **Web框架**: FastAPI
- **音频处理**: OpenAI Whisper
- **新闻抓取**: newspaper3k
- **向量数据库**: Qdrant
- **文本嵌入**: SentenceTransformers
- **任务调度**: APScheduler

## 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd mike-server
```

### 2. 安装依赖
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 3. 启动Qdrant
```bash
docker run -d -p 6333:6333 qdrant/qdrant:latest
```

### 4. 配置环境变量
```bash
cp env.example .env
# 编辑.env文件配置必要参数
```

### 5. 启动服务
```bash
./scripts/start.sh
```

## 使用方式

### 音频转文字
```bash
curl -X POST "http://localhost:3000/api/audio/transcribe" \
  -F "audio_file=@audio.m4a"
```

### 搜索新闻
```bash
curl -X POST "http://localhost:3000/api/news/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "科技新闻",
    "cutoff_timestamp": "2024-01-15T10:00:00",
    "top_k": 5
  }'
```

### 管理调度器
```bash
# 启动调度器
curl -X POST "http://localhost:3000/api/admin/scheduler/start?secret=heymike"

# 查看状态
curl "http://localhost:3000/api/admin/scheduler/status?secret=heymike"
```

## API文档

启动服务后访问：http://localhost:3000/docs

## 部署

### Docker部署（推荐）
```bash
cd docker
docker-compose up -d --build
```

### 传统部署
```bash
./scripts/start.sh
```

## 配置说明

### 环境变量
- `ADMIN_SECRET`: 管理员密钥（默认：heymike）
- `QDRANT_HOST`: Qdrant主机地址
- `QDRANT_PORT`: Qdrant端口
- `WHISPER_MODEL`: Whisper模型大小
- `AUTO_START_SCHEDULER`: 是否自动启动调度器

### 团队配置
在`.env`文件中配置`TEAM_IDS`来指定要抓取新闻的团队。

## 项目结构

```
mike-server/
├── src/                    # 源代码
│   ├── config/            # 配置管理
│   ├── models/            # 数据模型
│   ├── routes/            # API路由
│   ├── services/          # 业务逻辑
│   ├── utils/             # 工具函数
│   └── scripts/           # 独立脚本
├── tests/                 # 测试代码
├── docs/                  # 文档
├── scripts/               # 部署脚本
└── docker/                # Docker配置
```

## 开发

### 运行测试
```bash
pytest
```

### 代码格式化
```bash
black src/
isort src/
```

### 独立运行调度器
```bash
python src/scripts/run_scheduler.py
```

## 监控和日志

- 应用日志：`logs/app.log`
- 调度器日志：`logs/scheduler.log`
- 健康检查：`/health`
- 调度器状态：`/api/admin/scheduler/status`

## 故障排除

### 常见问题
1. **Qdrant连接失败**: 检查Docker服务是否运行
2. **模型下载失败**: 检查网络连接和磁盘空间
3. **权限问题**: 确保脚本有执行权限

### 获取帮助
- 查看日志文件
- 检查健康检查端点
- 参考部署文档

## 贡献

欢迎提交Issue和Pull Request！

## 许可证

MIT License
