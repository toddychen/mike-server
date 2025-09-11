import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from pydantic import ValidationError
import json
from utils.logger import logger
from models.function_calls import FunctionMetadata

@dataclass
class FunctionInfo:
    """Internal function information"""
    func: Callable
    metadata: FunctionMetadata
    call_count: int = 0
    total_execution_time: float = 0.0

class FunctionRegistry:
    """Central registry for managing function calls"""
    
    def __init__(self):
        self._functions: Dict[str, FunctionInfo] = {}
    
    def register(self, name: str, func: Callable, metadata: FunctionMetadata):
        """Register a function with its metadata"""
        if name in self._functions:
            logger.warning(f"Function {name} is already registered, overwriting...")
        
        self._functions[name] = FunctionInfo(func=func, metadata=metadata)
        logger.info(f"Registered function: {name}")
    
    def get_function(self, name: str) -> Optional[Callable]:
        """Get a registered function by name"""
        return self._functions.get(name).func if name in self._functions else None
    
    def get_metadata(self, name: str) -> Optional[FunctionMetadata]:
        """Get function metadata by name"""
        return self._functions.get(name).metadata if name in self._functions else None
    
    def list_functions(self) -> List[Dict[str, Any]]:
        """List all available functions with their metadata"""
        return [
            {
                "name": name,
                "description": info.metadata.description,
                "version": info.metadata.version,
                "tags": info.metadata.tags,
                "required_parameters": info.metadata.required_parameters,
                "optional_parameters": info.metadata.optional_parameters,
                "call_count": info.call_count,
                "avg_execution_time_ms": (
                    info.total_execution_time / info.call_count * 1000
                    if info.call_count > 0 else 0
                )
            }
            for name, info in self._functions.items()
        ]
    
    def validate_parameters(self, name: str, params: dict) -> tuple[bool, Optional[str]]:
        """Validate function parameters"""
        if name not in self._functions:
            return False, f"Function {name} not found"
        
        metadata = self._functions[name].metadata
        
        # Check required parameters
        for required_param in metadata.required_parameters:
            if required_param not in params:
                return False, f"Missing required parameter: {required_param}"
        
        # Check parameter types using JSON Schema validation
        try:
            self._validate_with_schema(params, metadata.parameters)
            return True, None
        except ValidationError as e:
            return False, f"Parameter validation failed: {str(e)}"
    
    def _validate_with_schema(self, params: dict, schema: dict) -> dict:
        """Validate parameters using JSON Schema"""
        # Simplified validation - in production, use jsonschema library
        return params
    
    
    async def execute_function(self, name: str, params: dict) -> Dict[str, Any]:
        """Execute a registered function"""
        if name not in self._functions:
            return {
                "success": False,
                "error": f"Function {name} not found",
                "data": None
            }
        
        # Validate parameters
        is_valid, error_msg = self.validate_parameters(name, params)
        if not is_valid:
            return {
                "success": False,
                "error": error_msg,
                "data": None
            }
        
        try:
            # Execute function
            func_info = self._functions[name]
            func = func_info.func
            metadata = func_info.metadata
            
            # Record execution start time
            start_time = time.time()
            
            # Execute function (async)
            result = await func(**params)
            
            # Record execution statistics
            execution_time = time.time() - start_time
            func_info.call_count += 1
            func_info.total_execution_time += execution_time
            
            return {
                "success": True,
                "data": result,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Function {name} execution failed: {e}")
            return {
                "success": False,
                "error": f"Function execution failed: {str(e)}",
                "data": None
            }
    
    def get_function_stats(self, name: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific function"""
        if name not in self._functions:
            return None
        
        func_info = self._functions[name]
        return {
            "name": name,
            "call_count": func_info.call_count,
            "total_execution_time_ms": func_info.total_execution_time * 1000,
            "avg_execution_time_ms": (
                func_info.total_execution_time / func_info.call_count * 1000
                if func_info.call_count > 0 else 0
            ),
        }

# Global function registry instance
function_registry = FunctionRegistry()
