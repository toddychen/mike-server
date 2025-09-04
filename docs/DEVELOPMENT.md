# Mike Server 开发文档

## 项目结构

```
mike-server/
├── src/                    # 源代码目录
│   ├── config/            # 配置管理
│   ├── models/            # 数据模型
│   ├── routes/            # API路由
│   ├── services/          # 业务逻辑服务
│   ├── utils/             # 工具函数
│   └── scripts/           # 独立脚本
├── tests/                 # 测试代码
├── docs/                  # 文档
├── scripts/               # 部署脚本
├── docker/                # Docker配置
└── logs/                  # 日志文件
```

## 开发环境设置

### 1. 克隆项目
```bash
git clone <repository-url>
cd mike-server
```

### 2. 创建虚拟环境
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

### 3. 安装开发依赖
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 如果存在
```

### 4. 安装预提交钩子
```bash
pre-commit install
```

## 代码规范

### Python代码风格
- 遵循PEP 8规范
- 使用类型注解
- 函数和类必须有文档字符串
- 行长度限制：88字符（black格式化）

### 导入顺序
```python
# 标准库
import os
import sys
from typing import List, Dict

# 第三方库
import fastapi
from pydantic import BaseModel

# 本地模块
from .models import NewsContent
from ..utils.helpers import format_text
```

### 命名规范
- 类名：PascalCase（如`NewsScraperService`）
- 函数和变量：snake_case（如`fetch_news`）
- 常量：UPPER_CASE（如`MAX_FILE_SIZE`）
- 私有方法：下划线前缀（如`_validate_content`）

## 开发工作流

### 1. 创建新功能分支
```bash
git checkout -b feature/news-scraper
```

### 2. 开发功能
- 编写代码
- 添加测试
- 更新文档

### 3. 代码审查
```bash
# 运行测试
pytest

# 代码格式化
black src/
isort src/

# 类型检查
mypy src/

# 代码质量检查
flake8 src/
```

### 4. 提交代码
```bash
git add .
git commit -m "feat: 添加新闻抓取功能"
```

### 5. 合并到主分支
```bash
git checkout main
git merge feature/news-scraper
```

## 测试指南

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_news.py

# 运行特定测试类
pytest tests/test_news.py::TestNewsScraper

# 运行特定测试方法
pytest tests/test_news.py::TestNewsScraper::test_scraper_initialization

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

### 测试结构
```python
class TestNewsScraper:
    def setup_method(self):
        """每个测试方法前的设置"""
        self.scraper = NewsScraperService()
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        pass
    
    def test_scraper_initialization(self):
        """测试新闻抓取器初始化"""
        assert self.scraper is not None
```

### 测试最佳实践
1. 每个测试只测试一个功能点
2. 使用描述性的测试名称
3. 测试应该独立，不依赖其他测试
4. 使用mock避免外部依赖
5. 测试异常情况

## 日志规范

### 日志级别
- `DEBUG`: 详细的调试信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息
- `CRITICAL`: 严重错误

### 日志格式
```python
import logging

logger = logging.getLogger(__name__)

def process_news(url: str):
    logger.info(f"开始处理新闻: {url}")
    try:
        # 处理逻辑
        logger.info(f"新闻处理成功: {url}")
    except Exception as e:
        logger.error(f"新闻处理失败 {url}: {e}")
        raise
```

## 错误处理

### 异常类型
```python
from fastapi import HTTPException

class NewsProcessingError(Exception):
    """新闻处理错误"""
    pass

def process_news(url: str):
    try:
        # 处理逻辑
        pass
    except NewsProcessingError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"未知错误: {e}")
        raise HTTPException(status_code=500, detail="内部服务器错误")
```

### 错误响应格式
```python
{
    "detail": "错误描述",
    "error_code": "ERROR_CODE",
    "timestamp": "2024-01-15T10:00:00"
}
```

## 性能优化

### 1. 异步编程
```python
async def fetch_news_batch(urls: List[str]):
    """批量获取新闻"""
    tasks = [fetch_single_news(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 2. 缓存策略
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_embedding_model():
    """缓存embedding模型"""
    return SentenceTransformer('all-mpnet-base-v2')
```

### 3. 批量处理
```python
async def batch_store_news(news_list: List[NewsContent]):
    """批量存储新闻"""
    # 分批处理，避免内存溢出
    batch_size = 100
    for i in range(0, len(news_list), batch_size):
        batch = news_list[i:i+batch_size]
        await process_batch(batch)
```

## 配置管理

### 环境变量
```python
from .config.settings import settings

class NewsService:
    def __init__(self):
        self.api_key = settings.news_api_key
        self.base_url = settings.news_api_base_url
```

### 配置验证
```python
from pydantic import BaseSettings, validator

class Settings(BaseSettings):
    port: int = 3000
    
    @validator('port')
    def validate_port(cls, v):
        if v < 1024 or v > 65535:
            raise ValueError('端口必须在1024-65535之间')
        return v
```

## 文档更新

### API文档
- 更新`docs/API.md`
- 添加新的端点说明
- 更新请求/响应示例

### 部署文档
- 更新`docs/DEPLOYMENT.md`
- 添加新的配置选项
- 更新故障排除指南

### 代码注释
```python
def process_news_content(content: str) -> str:
    """
    处理新闻内容
    
    Args:
        content: 原始新闻内容
        
    Returns:
        处理后的新闻内容
        
    Raises:
        ValueError: 当内容为空时
    """
    if not content:
        raise ValueError("新闻内容不能为空")
    
    # 处理逻辑
    return processed_content
```

## 调试技巧

### 1. 使用pdb调试
```python
import pdb

def debug_function():
    pdb.set_trace()  # 设置断点
    # 代码在这里暂停
```

### 2. 日志调试
```python
logger.debug(f"变量值: {variable}")
logger.debug(f"函数调用: {function_name}({args})")
```

### 3. 性能分析
```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 要分析的代码
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats()
```

## 贡献指南

### 提交信息格式
```
type(scope): description

[optional body]

[optional footer]
```

类型：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码格式
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具的变动

### 代码审查清单
- [ ] 代码符合项目规范
- [ ] 添加了必要的测试
- [ ] 更新了相关文档
- [ ] 通过了所有测试
- [ ] 代码审查通过
