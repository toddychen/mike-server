from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from models.news import NewsSearchQuery
from services.news_storage import NewsStorage
from datetime import datetime
import logging

router = APIRouter()
vector_db = NewsStorage()

@router.post("/search")
async def search_news(query: NewsSearchQuery):
    """
    Search for similar news
    
    Args:
        query: Search query containing query text, timestamp filters and return count
        
    Returns:
        JSON response containing list of similar news
    """
    try:
        # Search for similar news
        results = vector_db.search_similar_news(query)
        
        return JSONResponse(content={
            "success": True,
            "query": {
                "text": query.query_text,
                "before": query.before.isoformat() if query.before else None,
                "after": query.after.isoformat() if query.after else None,
                "top_k": query.top_k
            },
            "results": results,
            "total_found": len(results)
        })
        
    except Exception as e:
        import traceback
        error_msg = f"News search failed: {e}"
        stack_trace = traceback.format_exc()
        
        # Log detailed error information
        logging.error(error_msg)
        logging.error(f"Error stack trace:\n{stack_trace}")
        
        # Return detailed error information
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}\nStack trace: {stack_trace}"
        )

@router.get("/health")
async def vector_db_health():
    """Check vector database health status"""
    try:
        # Simple health check
        collection_info = vector_db.get_collection_info()
        
        return {
            "status": "OK",
            "vector_db": "connected",
            "collection_info": collection_info
        }
    except Exception as e:
        logging.error(f"Vector database health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Vector database connection failed: {str(e)}"
        )

@router.get("/stats")
async def get_news_stats():
    """Get news statistics information"""
    try:
        stats = vector_db.get_collection_info()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logging.error(f"Failed to get statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )
