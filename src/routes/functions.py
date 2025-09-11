from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from function_calling.function_registry import function_registry
from models.function_calls import (
    FunctionCallRequest, 
    FunctionCallResponse, 
    FunctionMetadataResponse
)
from utils.logger import logger
import time

router = APIRouter()

@router.post("/call", response_model=FunctionCallResponse)
async def call_function(request: FunctionCallRequest):
    """Execute a function call"""
    start_time = time.time()
    
    try:
        logger.info(f"Executing function call: {request.function_name}")
        
        result = await function_registry.execute_function(
            request.function_name,
            request.parameters
        )
        
        execution_time = (time.time() - start_time) * 1000
        
        response = FunctionCallResponse(
            success=result["success"],
            data=result["data"],
            error=result["error"],
            function_name=request.function_name,
            execution_time_ms=execution_time
        )
        
        if result["success"]:
            logger.info(f"Function {request.function_name} executed successfully in {execution_time:.2f}ms")
        else:
            logger.warning(f"Function {request.function_name} failed: {result['error']}")
        
        return response
        
    except Exception as e:
        logger.error(f"Function call failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tools")
async def get_tools():
    """Get functions in tools format"""
    try:
        functions = function_registry.list_functions()
        tools = []
        
        for func in functions:
            # Get the full metadata for this function
            metadata = function_registry.get_metadata(func["name"])
            if metadata:
                tool = {
                    "type": "function",
                    "name": metadata.name,
                    "description": metadata.description,
                    "parameters": metadata.parameters
                }
                tools.append(tool)
        
        return tools
    except Exception as e:
        logger.error(f"Failed to get tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{function_name}/metadata", response_model=FunctionMetadataResponse)
async def get_function_metadata(function_name: str):
    """Get metadata for a specific function"""
    try:
        metadata = function_registry.get_metadata(function_name)
        if not metadata:
            raise HTTPException(
                status_code=404, 
                detail=f"Function {function_name} not found"
            )
        
        return FunctionMetadataResponse(
            name=metadata.name,
            description=metadata.description,
            version=metadata.version,
            parameters=metadata.parameters,
            required_parameters=metadata.required_parameters,
            optional_parameters=metadata.optional_parameters,
            timeout_seconds=metadata.timeout_seconds,
            rate_limit_per_minute=metadata.rate_limit_per_minute,
            tags=metadata.tags,
            external_api_url=metadata.external_api_url
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get metadata for {function_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{function_name}/stats")
async def get_function_stats(function_name: str):
    """Get statistics for a specific function"""
    try:
        stats = function_registry.get_function_stats(function_name)
        if not stats:
            raise HTTPException(
                status_code=404,
                detail=f"Function {function_name} not found"
            )
        
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get stats for {function_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def functions_health_check():
    """Health check for functions service"""
    try:
        function_count = len(function_registry.list_functions())
        return {
            "status": "healthy",
            "registered_functions": function_count,
            "message": "Functions service is running"
        }
    except Exception as e:
        logger.error(f"Functions health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
