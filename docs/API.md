# Mike Server API 文档

## 概述

Mike Server 是一个集成了音频转文字和新闻搜索功能的Web服务，使用本地Whisper模型和向量数据库。

## 基础信息

- **基础URL**: `http://localhost:3000`
- **API文档**: `http://localhost:3000/docs`
- **健康检查**: `http://localhost:3000/health`

## 认证

管理API需要secret key认证，在URL参数中传递 `secret=heymike`

## API端点

### 1. 音频转文字 API

#### POST /api/audio/transcribe
将音频文件转换为文字

**请求**:
- Content-Type: `multipart/form-data`
- Body: `audio_file` (音频文件)

**响应**:
```json
{
  "success": true,
  "transcription": "转换后的文字内容",
  "language": "zh",
  "segments": [...],
  "filename": "audio.m4a",
  "file_size": 1024000,
  "model": "tiny",
  "method": "memory_processing",
  "performance_metrics": {...}
}
```

#### GET /api/audio/supported-formats
获取支持的音频格式

#### GET /api/audio/models
获取可用的Whisper模型

#### POST /api/audio/change-model/{model_name}
切换Whisper模型

### 2. 新闻搜索 API

#### POST /api/news/search
搜索相似新闻

**请求**:
```json
{
  "query_text": "搜索查询文本",
  "cutoff_timestamp": "2024-01-15T10:00:00",
  "top_k": 10
}
```

**响应**:
```json
{
  "success": true,
  "query": {...},
  "results": [
    {
      "id": "uuid",
      "score": 0.85,
      "url": "https://example.com/news1",
      "title": "新闻标题",
      "content": "新闻内容...",
      "summary": "新闻摘要",
      "published_at": "2024-01-15T09:00:00",
      "team_id": "team1",
      "source": "新闻源",
      "updated_at": "2024-01-15T10:00:00"
    }
  ],
  "total_found": 10
}
```

#### GET /api/news/health
检查向量数据库健康状态

#### GET /api/news/stats
获取新闻统计信息

### 3. 管理 API

#### GET /api/admin/scheduler/status?secret=heymike
获取调度器状态

#### POST /api/admin/scheduler/start?secret=heymike
启动调度器

#### POST /api/admin/scheduler/stop?secret=heymike
停止调度器

#### POST /api/admin/scheduler/trigger?secret=heymike
手动触发新闻抓取

#### GET /api/admin/scheduler/config?secret=heymike
获取调度器配置

#### POST /api/admin/scheduler/restart?secret=heymike
重启调度器

#### GET /api/admin/scheduler/stats?secret=heymike
获取调度器和集合统计信息

## 错误处理

所有API都返回标准的HTTP状态码：

- `200`: 成功
- `400`: 请求参数错误
- `403`: 认证失败
- `500`: 服务器内部错误

错误响应格式：
```json
{
  "detail": "错误描述"
}
```

## 使用示例

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

### 启动调度器
```bash
curl -X POST "http://localhost:3000/api/admin/scheduler/start?secret=heymike"
```

### 获取状态
```bash
curl "http://localhost:3000/api/admin/scheduler/status?secret=heymike"
```
