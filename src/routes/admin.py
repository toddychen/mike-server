from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from services.scheduler import NewsSchedulerService
from services.news_storage import NewsStorage
from config.settings import settings
import logging

router = APIRouter()
news_scheduler = NewsSchedulerService()
vector_db = NewsStorage()

def verify_secret_key(secret: str = Query(..., description="Secret key for admin access")):
    """Verify secret key"""
    expected_secret = settings.admin_secret
    if secret != expected_secret:
        raise HTTPException(
            status_code=403, 
            detail="Invalid secret key"
        )
    return True

@router.get("/scheduler/status")
async def get_scheduler_status(secret: str = Query(..., alias="secret")):
    """Get scheduler status"""
    verify_secret_key(secret)
    try:
        status = news_scheduler.get_status()
        return JSONResponse(content={
            "success": True,
            "scheduler_status": status,
            "message": "Status query successful"
        })
    except Exception as e:
        logging.error(f"Failed to get scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")

@router.post("/scheduler/start")
async def start_scheduler(secret: str = Query(..., alias="secret")):
    """Start scheduler"""
    verify_secret_key(secret)
    try:
        await news_scheduler.start_scheduler()
        return JSONResponse(content={
            "success": True,
            "message": "Scheduler started"
        })
    except Exception as e:
        logging.error(f"Failed to start scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start: {str(e)}")

@router.post("/scheduler/stop")
async def stop_scheduler(secret: str = Query(..., alias="secret")):
    """Stop scheduler"""
    verify_secret_key(secret)
    try:
        await news_scheduler.stop_scheduler()
        return JSONResponse(content={
            "success": True,
            "message": "Scheduler stopped"
        })
    except Exception as e:
        logging.error(f"Failed to stop scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop: {str(e)}")

@router.post("/scheduler/trigger")
async def trigger_news_fetch(secret: str = Query(..., alias="secret")):
    """Manually trigger news fetch"""
    verify_secret_key(secret)
    try:
        success = news_scheduler.manual_trigger()
        if success:
            return JSONResponse(content={
                "success": True,
                "message": "News fetch task triggered"
            })
        else:
            raise HTTPException(status_code=400, detail="Scheduler not running")
    except Exception as e:
        logging.error(f"Manual trigger failed: {e}")
        raise HTTPException(status_code=500, detail=f"Trigger failed: {str(e)}")

@router.get("/scheduler/config")
async def get_scheduler_config(secret: str = Query(..., alias="secret")):
    """Get scheduler configuration"""
    verify_secret_key(secret)
    try:
        config = {
            "team_ids": news_scheduler.team_ids,
            "is_running": news_scheduler.is_running,
            "next_run_time": None
        }
        
        # Get next run time
        if news_scheduler.is_running:
            jobs = news_scheduler.scheduler.get_jobs()
            for job in jobs:
                if job.id == "news_fetch_job":
                    config["next_run_time"] = str(job.next_run_time) if job.next_run_time else None
                    break
        
        return JSONResponse(content={
            "success": True,
            "config": config
        })
    except Exception as e:
        logging.error(f"Failed to get scheduler config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get config: {str(e)}")

@router.post("/scheduler/restart")
async def restart_scheduler(secret: str = Query(..., alias="secret")):
    """Restart scheduler"""
    verify_secret_key(secret)
    try:
        # Stop first
        await news_scheduler.stop_scheduler()
        # Then start
        await news_scheduler.start_scheduler()
        
        return JSONResponse(content={
            "success": True,
            "message": "Scheduler restarted"
        })
    except Exception as e:
        logging.error(f"Failed to restart scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to restart: {str(e)}")

@router.get("/scheduler/stats")
async def get_scheduler_stats(secret: str = Query(..., alias="secret")):
    """Get scheduler and collection statistics"""
    verify_secret_key(secret)
    try:
        stats = await news_scheduler.get_collection_stats()
        return JSONResponse(content={
            "success": True,
            "stats": stats
        })
    except Exception as e:
        logging.error(f"Failed to get statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

@router.post("/database/clear")
async def clear_database(secret: str = Query(..., alias="secret")):
    """Clear vector database collection"""
    verify_secret_key(secret)
    try:
        # Get current collection info
        collection_info = vector_db.get_collection_info()
        points_count = collection_info['points_count']
        
        if points_count == 0:
            return JSONResponse(content={
                "success": True,
                "message": "Database is already empty",
                "collection_info": collection_info
            })
        
        # Clear the collection
        success = vector_db.clear_collection()
        
        if success:
            # Get updated collection info
            new_info = vector_db.get_collection_info()
            
            return JSONResponse(content={
                "success": True,
                "message": f"Successfully cleared database, deleted {points_count} data points",
                "previous_count": points_count,
                "current_count": new_info['points_count'],
                "collection_info": new_info
            })
        else:
            raise HTTPException(status_code=500, detail="Failed to clear database")
            
    except Exception as e:
        logging.error(f"Failed to clear database: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear database: {str(e)}")

@router.get("/database/point/{content_id}")
async def get_point_by_content_id(content_id: str):
    """Get a point by its content_id"""
    try:
        point_data = vector_db.get_point_by_content_id(content_id)
        
        if point_data:
            return JSONResponse(content={
                "success": True,
                "message": f"Point found with content_id: {content_id}",
                "data": point_data
            })
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": f"No point found with content_id: {content_id}",
                    "data": None
                }
            )
            
    except Exception as e:
        logging.error(f"Failed to get point with content_id {content_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get point: {str(e)}")

@router.delete("/database/point/{content_id}")
async def delete_point_by_content_id(
    content_id: str, 
    secret: str = Query(..., alias="secret")
):
    """Delete a point by its content_id"""
    verify_secret_key(secret)
    try:
        # First check if point exists
        point_data = vector_db.get_point_by_content_id(content_id)
        
        if not point_data:
            return JSONResponse(
                status_code=404,
                content={
                    "success": False,
                    "message": f"Cannot delete: no point found with content_id: {content_id}",
                    "data": None
                }
            )
        
        # Delete the point
        success = vector_db.delete_point_by_content_id(content_id)
        
        if success:
            return JSONResponse(content={
                "success": True,
                "message": f"Successfully deleted point with content_id: {content_id}",
                "deleted_point": point_data
            })
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete point with content_id: {content_id}")
            
    except Exception as e:
        logging.error(f"Failed to delete point with content_id {content_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete point: {str(e)}")
