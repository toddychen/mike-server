from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import os
from ..services.whisper_service import WhisperService

router = APIRouter()
whisper_service = WhisperService()

@router.post("/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...)):
    """
    接收音频文件并转换为文字，返回详细元数据
    
    Args:
        audio_file: 上传的音频文件
        
    Returns:
        JSON响应，包含转换结果和元数据
    """
    # 检查文件类型
    if not audio_file.content_type or not audio_file.content_type.startswith('audio/'):
        raise HTTPException(
            status_code=400, 
            detail="只支持音频文件格式"
        )
    
    # 检查文件大小 (默认10MB)
    max_size = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB
    if audio_file.size and audio_file.size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小不能超过 {max_size // 1024 // 1024}MB"
        )
    
    try:
        # 读取音频文件内容到内存
        content = await audio_file.read()
        
        # 转换音频并获取元数据，传递文件名以确定正确的扩展名
        result = whisper_service.transcribe_audio(content, audio_file.filename)
        
        return JSONResponse(content={
            "success": True,
            "transcription": result["text"],
            "language": result["language"],
            "segments": result["segments"],
            "filename": audio_file.filename,
            "file_size": len(content),
            "model": result["model"],
            "method": "memory_processing",
            "performance_metrics": result.get("performance_metrics", {})
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音频转换失败: {str(e)}")

@router.get("/supported-formats")
async def get_supported_formats():
    """获取支持的音频格式"""
    return {
        "supported_formats": [
            "mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"
        ],
        "max_file_size": f"{int(os.getenv('MAX_FILE_SIZE', 10485760)) // 1024 // 1024}MB"
    }

@router.get("/models")
async def get_available_models():
    """获取可用的Whisper模型"""
    return {
        "current_model": whisper_service.model_name,
        "available_models": whisper_service.get_available_models(),
        "model_info": {
            "tiny": "最快，准确度较低",
            "base": "平衡速度和准确度",
            "small": "较好准确度",
            "medium": "高准确度",
            "large": "最高准确度，最慢"
        }
    }

@router.post("/change-model/{model_name}")
async def change_model(model_name: str):
    """切换Whisper模型"""
    success = whisper_service.change_model(model_name)
    if success:
        return {"success": True, "message": f"模型已切换到: {model_name}"}
    else:
        raise HTTPException(status_code=400, detail="模型切换失败")
