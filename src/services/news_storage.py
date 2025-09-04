import logging
import os
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from models.news import NewsContent, NewsSearchQuery
from config.settings import settings

# Set PyTorch memory allocator configuration to avoid "invalid low watermark ratio" error
os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:128'

class NewsStorage:
    def __init__(self, host: str = None, port: int = None):
        # Initialize logger
        self.logger = logging.getLogger(__name__)
        
        self.host = host or settings.qdrant_host
        self.port = port or settings.qdrant_port
        self.client = QdrantClient(host=self.host, port=self.port)
        self.collection_name = settings.qdrant_collection
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('all-mpnet-base-v2', device='cpu')  # 768 dimensions, recommended
        self.vector_size = self.embedding_model.get_sentence_embedding_dimension()
        
        # Ensure collection exists
        self._ensure_collection()
        
        self.logger.info(f"Vector database service initialized, using model: all-mpnet-base-v2, vector dimension: {self.vector_size}")
    
    def _ensure_collection(self):
        """Ensure collection exists"""
        try:
            # First try to get the collection
            collection_info = self.client.get_collection(self.collection_name)
            self.logger.info(f"Collection {self.collection_name} already exists")
            return
        except Exception as e:
            # Collection doesn't exist, create it
            self.logger.info(f"Collection {self.collection_name} not found, creating new one...")
        
        try:
            # Create new collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size, 
                    distance=Distance.COSINE
                )
            )
            self.logger.info(f"Successfully created collection: {self.collection_name}")
        except Exception as e:
            self.logger.error(f"Failed to create collection {self.collection_name}: {e}")
            raise
    
    def store_news(self, news_content: NewsContent) -> bool:
        """Store news to vector database, using ContentId for deduplication"""
        try:
            # Check if already exists (deduplication based on ContentId)
            existing_points = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="content_id",
                            match=MatchValue(value=news_content.content_id)
                        )
                    ]
                ),
                limit=1
            )
            
            if existing_points[0]:  # If already exists, do not allow duplicate storage
                self.logger.error(f"❌ News already exists in database: {news_content.metadata.title} (content_id: {news_content.content_id})")
                return True
            else:  # If not exists, create new point
                # Generate text embedding using summary instead of full content
                text_for_embedding = f"{news_content.metadata.title} {news_content.summary}"
                embedding = self.embedding_model.encode(text_for_embedding).tolist()
                
                # Create new point
                point = PointStruct(
                    id=abs(hash(news_content.content_id)) % (2**63),  # Use absolute hash of ContentId to ensure positive and within 2^63
                    vector=embedding,
                    payload={
                        "content_id": news_content.content_id,
                        "url": news_content.metadata.url,
                        "title": news_content.metadata.title,
                        "content": news_content.content,
                        "summary": news_content.summary,
                        "extracted_entities": news_content.extracted_entities,
                        "published_at": news_content.metadata.published_at.isoformat() if news_content.metadata.published_at else None,
                        "entity_id": news_content.metadata.entity_id,
                        "source": news_content.metadata.source,
                        "content_type": news_content.metadata.content_type,
                        "updated_at": news_content.updated_at.isoformat()
                    }
                )
                
                # Log payload sent to Qdrant
                self.logger.info(f"📤 Sending payload to Qdrant for news: <{news_content.metadata.title}>")
                # self.logger.info(f"📋 Summary in payload: {point.payload.get('summary', 'NO_SUMMARY')[:100]}...")
                # self.logger.info(f"📋 Summary length: {len(point.payload.get('summary', ''))} characters")
                
                # Store to Qdrant
                self.client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
                #self.logger.info(f"Storing new news: {news_content.metadata.title}")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to store news: {e}")
            return False
    
    def search_similar_news(self, query: NewsSearchQuery) -> List[Dict]:
        """Search for similar news"""
        try:
            # Generate embedding for query text
            query_embedding = self.embedding_model.encode(query.query_text).tolist()
            
            # Build filter conditions
            filter_conditions = []
            
            # Time filters
            if query.before:
                # publish_date < before
                filter_conditions.append(
                    FieldCondition(
                        key="published_at",
                        range={"lt": query.before.isoformat()}
                    )
                )
            
            if query.after:
                # publish_date >= after
                filter_conditions.append(
                    FieldCondition(
                        key="published_at",
                        range={"gte": query.after.isoformat()}
                    )
                )
            
            # Execute search
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                query_filter=Filter(must=filter_conditions) if filter_conditions else None,
                limit=query.top_k,
                with_payload=True
            )
            
            # Format results
            results = []
            for point in search_result:
                results.append({
                    'content_id': point.payload.get('content_id'),
                    'title': point.payload.get('title'),
                    'content': point.payload.get('content'),
                    'summary': point.payload.get('summary'),  # Include summary in search results
                    'url': point.payload.get('url'),
                    'published_at': point.payload.get('published_at'),
                    'entity_id': point.payload.get('entity_id'),
                    'source': point.payload.get('source'),
                    'extracted_entities': point.payload.get('extracted_entities'),
                    'score': point.score
                })
            
            self.logger.info(f"Search completed, found {len(results)} similar news")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to search similar news: {e}")
            import traceback
            self.logger.error(f"Error stack trace: {traceback.format_exc()}")
            return []
    
    def get_collection_info(self) -> Dict:
        """Get collection information"""
        try:
            info = self.client.get_collection(self.collection_name)
            
            # Direct access to attributes - no need for hasattr
            return {
                "name": self.collection_name,  # Use our configured name
                "vector_size": info.config.params.vectors.size,
                "distance": str(info.config.params.vectors.distance),
                "points_count": info.points_count,
                "segments_count": info.segments_count,
                "status": str(info.status),
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get collection info: {e}")
            # Return basic info even if detailed info fails
            return {
                "name": self.collection_name,
                "vector_size": self.vector_size,
                "distance": "Cosine",
                "points_count": 0,
                "status": "basic_info_only"
            }
    
    def clear_collection(self) -> bool:
        """Clear all points from the collection by deleting and recreating it"""
        try:
            # Get current collection info
            collection_info = self.client.get_collection(self.collection_name)
            points_count = collection_info.points_count
            
            if points_count == 0:
                self.logger.info(f"Collection '{self.collection_name}' is already empty")
                return True
            
            self.logger.info(f"Clearing {points_count} points from collection '{self.collection_name}'")
            
            # Get collection configuration
            vector_size = collection_info.config.params.vectors.size
            distance = collection_info.config.params.vectors.distance
            
            # Delete collection
            self.client.delete_collection(self.collection_name)
            self.logger.info(f"Collection '{self.collection_name}' deleted")
            
            # Recreate collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE if distance == "Cosine" else Distance.EUCLID
                )
            )
            self.logger.info(f"Collection '{self.collection_name}' recreated with same configuration")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear collection: {e}")
            return False
    
    def get_point_by_content_id(self, content_id: str) -> Optional[Dict]:
        """Get a point by its metadata's content_id"""
        try:
            # Search for point with specific content_id
            search_result = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="content_id",
                            match=MatchValue(value=content_id)
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
                with_vectors=False
            )
            
            if search_result[0] and len(search_result[0]) > 0:
                point = search_result[0][0]
                self.logger.info(f"Found point with content_id: {content_id}")
                return {
                    'id': point.id,
                    'content_id': point.payload.get('content_id'),
                    'title': point.payload.get('title'),
                    'content': point.payload.get('content'),
                    'summary': point.payload.get('summary'),
                    'url': point.payload.get('url'),
                    'published_at': point.payload.get('published_at'),
                    'entity_id': point.payload.get('entity_id'),
                    'source': point.payload.get('source'),
                    'content_type': point.payload.get('content_type'),
                    'updated_at': point.payload.get('updated_at'),
                    'extracted_entities': point.payload.get('extracted_entities')
                }
            else:
                self.logger.info(f"No point found with content_id: {content_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get point by content_id {content_id}: {e}")
            return None
    
    def delete_point_by_content_id(self, content_id: str) -> bool:
        """Delete a point by its metadata's content_id"""
        try:
            # First find the point to get its ID
            point_data = self.get_point_by_content_id(content_id)
            
            if not point_data:
                self.logger.warning(f"Cannot delete: no point found with content_id: {content_id}")
                return False
            
            point_id = point_data['id']
            
            # Delete the point by ID
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=[point_id]
            )
            
            self.logger.info(f"Successfully deleted point with content_id: {content_id} (point_id: {point_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete point with content_id {content_id}: {e}")
            return False
    
    def get_points_without_extraction(self, limit: int = 10, get_all: bool = False) -> List[Dict]:
        """Get points that don't have extracted_entities field"""
        try:
            points_without_extraction = []
            
            if get_all:
                # Get all points using scroll with point ID offset
                page_size = 100  # Process in smaller batches
                offset = None  # Start with None for first scroll
                total_processed = 0
                max_iterations = 100  # Safety limit
                iteration_count = 0
                
                while iteration_count < max_iterations:
                    iteration_count += 1
                    
                    # Prepare scroll parameters
                    scroll_params = {
                        'collection_name': self.collection_name,
                        'limit': page_size,
                        'with_payload': True,
                        'with_vectors': False
                    }
                    
                    # Add offset only if we have one (not for first scroll)
                    if offset is not None:
                        scroll_params['offset'] = offset
                    
                    scroll_result = self.client.scroll(**scroll_params)
                    points = scroll_result[0]
                    
                    if not points:  # No more points
                        self.logger.info(f"No more points found, total processed: {total_processed}")
                        break
                    
                    for point in points:
                        total_processed += 1
                        
                        # Log each point's title for debugging
                        # title = point.payload.get('title', 'No title')
                        # self.logger.info(f"Processing point {total_processed}: {title}")
                        
                        # Check if the point has extracted_entities field
                        if 'extracted_entities' not in point.payload:
                            points_without_extraction.append({
                                'id': point.id,
                                'content_id': point.payload.get('content_id'),
                                'title': point.payload.get('title'),
                                'content': point.payload.get('content'),
                                'summary': point.payload.get('summary'),
                                'url': point.payload.get('url'),
                                'published_at': point.payload.get('published_at'),
                                'entity_id': point.payload.get('entity_id'),
                                'source': point.payload.get('source'),
                                'content_type': point.payload.get('content_type'),
                                'updated_at': point.payload.get('updated_at')
                            })
                    
                    # Update offset to the ID of the last point for next iteration
                    offset = points[-1].id if points else None
                    
                    self.logger.info(f"Processed {total_processed} points, found {len(points_without_extraction)} without extracted_entities (iteration {iteration_count})")
                    
                    # Safety check to avoid infinite loops
                    if len(points) < page_size:
                        self.logger.info(f"Received {len(points)} points (less than page_size {page_size}), stopping pagination")
                        break
                
                if iteration_count >= max_iterations:
                    self.logger.warning(f"Reached maximum iterations ({max_iterations}), stopping pagination. Total points processed: {total_processed}")
            else:
                # Get limited number of points
                scroll_result = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=limit,
                    with_payload=True,
                    with_vectors=False
                )
                
                for point in scroll_result[0]:
                    # Check if the point has extracted_entities field
                    if 'extracted_entities' not in point.payload:
                        points_without_extraction.append({
                            'id': point.id,
                            'content_id': point.payload.get('content_id'),
                            'title': point.payload.get('title'),
                            'content': point.payload.get('content'),
                            'summary': point.payload.get('summary'),
                            'url': point.payload.get('url'),
                            'published_at': point.payload.get('published_at'),
                            'entity_id': point.payload.get('entity_id'),
                            'source': point.payload.get('source'),
                            'content_type': point.payload.get('content_type'),
                            'updated_at': point.payload.get('updated_at')
                        })
            
            self.logger.info(f"Found {len(points_without_extraction)} points without extracted_entities field")
            return points_without_extraction
            
        except Exception as e:
            self.logger.error(f"Failed to get points without extraction: {e}")
            return []
    
    def update_point_extracted_entities(self, content_id: str, extracted_entities: Dict) -> bool:
        """Update a point's extracted_entities field"""
        try:
            # First find the point to get its ID
            point_data = self.get_point_by_content_id(content_id)
            
            if not point_data:
                self.logger.warning(f"Cannot update: no point found with content_id: {content_id}")
                return False
            
            point_id = point_data['id']
            
            # Update the point with extracted_entities
            self.client.set_payload(
                collection_name=self.collection_name,
                payload={
                    "extracted_entities": extracted_entities,
                    "updated_at": point_data['updated_at']  # Keep existing updated_at for backfill
                },
                points=[point_id]
            )
            
            self.logger.info(f"Successfully updated point {content_id} with extracted_entities")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update point {content_id} with extracted_entities: {e}")
            return False
