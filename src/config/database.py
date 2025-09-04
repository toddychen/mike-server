from qdrant_client import QdrantClient
from config.settings import settings
import logging

def get_qdrant_client() -> QdrantClient:
    """获取Qdrant客户端连接"""
    try:
        client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port
        )
        # 测试连接
        client.get_collections()
        logging.info("Qdrant连接成功")
        return client
    except Exception as e:
        logging.error(f"Qdrant连接失败: {e}")
        raise

def init_qdrant_collections():
    """初始化Qdrant集合"""
    try:
        client = get_qdrant_client()
        
        # 检查集合是否存在
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if settings.qdrant_collection not in collection_names:
            # 创建新闻集合
            from qdrant_client.models import Distance, VectorParams
            
            client.create_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=VectorParams(
                    size=768,  # 使用推荐的768维
                    distance=Distance.COSINE
                )
            )
            logging.info(f"创建集合: {settings.qdrant_collection}")
        else:
            logging.info(f"集合已存在: {settings.qdrant_collection}")
            
    except Exception as e:
        logging.error(f"初始化Qdrant集合失败: {e}")
        raise
