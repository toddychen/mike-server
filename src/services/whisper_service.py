import os
import whisper
import tempfile
import time
from dotenv import load_dotenv

load_dotenv()

class WhisperService:
    def __init__(self):
        """初始化本地Whisper服务"""
        self.model_name = os.getenv("WHISPER_MODEL", "tiny")
        print(f"🤖 正在加载Whisper模型: {self.model_name}")
        
        # 模型性能说明
        model_info = {
            "tiny": "39MB - 最快速度，适合实时处理",
            "base": "74MB - 平衡速度和准确度",
            "small": "244MB - 较好准确度",
            "medium": "769MB - 高准确度",
            "large": "1550MB - 最高准确度，最慢"
        }
        
        print(f"📊 模型信息: {model_info.get(self.model_name, '未知模型')}")
        
        try:
            # 加载本地Whisper模型
            self.model = whisper.load_model(self.model_name)
            print(f"✅ Whisper模型 {self.model_name} 加载成功")
            
            # 如果是tiny模型，给出性能提示
            if self.model_name == "tiny":
                print("⚡ 使用tiny模型 - 速度优先，适合低延迟场景")
            elif self.model_name == "base":
                print("⚖️  使用base模型 - 平衡速度和准确度")
            else:
                print(f"🎯 使用{self.model_name}模型 - 准确度优先")
                
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            # 如果指定模型失败，尝试加载tiny模型
            try:
                print("🔄 尝试加载备用模型: tiny")
                self.model = whisper.load_model("tiny")
                self.model_name = "tiny"
                print("✅ 使用备用模型: tiny")
            except Exception as e2:
                raise Exception(f"无法加载任何Whisper模型: {e2}")
    
    def transcribe_audio(self, audio_content: bytes, filename: str = None):
        """
        使用Whisper推荐的方式转换音频，返回详细元数据
        
        Args:
            audio_content: 音频文件的二进制内容
            filename: 原始文件名（用于确定正确的文件扩展名）
            
        Returns:
            包含转换结果和元数据的字典
        """
        temp_file = None
        total_start_time = time.time()
        
        try:
            file_size = len(audio_content)
            print(f"🎵 开始转换音频数据，大小: {file_size} 字节")
            
            # 1. 文件扩展名确定时间
            ext_start = time.time()
            if filename and '.' in filename:
                file_extension = filename.split('.')[-1].lower()
                # 确保扩展名是有效的音频格式
                valid_extensions = ['mp3', 'mp4', 'mpeg', 'mpga', 'm4a', 'wav', 'webm', 'aac']
                if file_extension in valid_extensions:
                    suffix = f".{file_extension}"
                else:
                    suffix = ".wav"  # 默认使用wav
            else:
                suffix = ".wav"  # 默认使用wav
            
            ext_time = time.time() - ext_start
            print(f"📁 使用文件扩展名: {suffix} (耗时: {ext_time:.3f}秒)")
            
            # 2. 临时文件创建时间
            temp_file_start = time.time()
            temp_file = tempfile.NamedTemporaryFile(
                delete=True,  # 自动删除
                suffix=suffix,  # 使用正确的扩展名
                mode='wb'
            )
            temp_file_time = time.time() - temp_file_start
            print(f"💾 临时文件创建耗时: {temp_file_time:.3f}秒")
            
            # 3. 文件写入时间
            write_start = time.time()
            temp_file.write(audio_content)
            temp_file.flush()  # 确保数据写入磁盘
            write_time = time.time() - write_start
            print(f"📝 文件写入耗时: {write_time:.3f}秒")
            
            print(f"💾 临时文件创建: {temp_file.name}")
            
            # 4. Whisper音频转换时间（核心处理）
            whisper_start = time.time()
            result = self.model.transcribe(temp_file.name)
            whisper_time = time.time() - whisper_start
            
            # 5. 结果处理时间
            process_start = time.time()
            transcription = result["text"].strip()
            process_time = time.time() - process_start
            
            # 总耗时
            total_time = time.time() - total_start_time
            
            print(f"✅ 音频转换完成，长度: {len(transcription)} 字符")
            
            # 详细时间分析
            print(f"\n⏱️  **服务器端时间分析**")
            print(f"  📁 扩展名确定: {ext_time:.3f}秒 ({ext_time/total_time*100:.1f}%)")
            print(f"  💾 临时文件创建: {temp_file_time:.3f}秒 ({temp_file_time/total_time*100:.1f}%)")
            print(f"  📝 文件写入: {write_time:.3f}秒 ({write_time/total_time*100:.1f}%)")
            print(f"  🎵 Whisper转换: {whisper_time:.3f}秒 ({whisper_time/total_time*100:.1f}%)")
            print(f"  📋 结果处理: {process_time:.3f}秒 ({process_time/total_time*100:.1f}%)")
            print(f"  🎯 总耗时: {total_time:.3f}秒")
            
            # 性能分析
            if whisper_time > total_time * 0.8:
                print(f"  🚀 Whisper转换是主要瓶颈 ({whisper_time/total_time*100:.1f}%)")
                if self.model_name != "tiny":
                    print(f"     建议: 使用更小的模型 (tiny)")
                else:
                    print(f"     已经是tiny模型，性能最优")
            elif write_time > total_time * 0.3:
                print(f"  💾 文件I/O是瓶颈 ({write_time/total_time*100:.1f}%)")
                print(f"     建议: 使用SSD存储，优化文件大小")
            else:
                print(f"  ✅ 性能表现良好")
            
            # 返回详细元数据
            return {
                "text": transcription,
                "language": result.get("language", "unknown"),
                "segments": result.get("segments", []),
                "model": self.model_name,
                "method": "file_path_processing",
                "performance_metrics": {
                    "total_time": total_time,
                    "whisper_time": whisper_time,
                    "file_io_time": temp_file_time + write_time,
                    "processing_time": ext_time + process_time
                }
            }
                    
        except Exception as e:
            total_time = time.time() - total_start_time
            print(f"❌ 音频转换失败，总耗时: {total_time:.3f}秒")
            raise Exception(f"音频转换失败: {str(e)}")
        finally:
            # 确保临时文件被关闭和删除
            if temp_file:
                temp_file.close()
                # 由于设置了 delete=True，文件会自动删除
    
    def get_available_models(self) -> list:
        """获取可用的Whisper模型列表"""
        return ["tiny", "base", "small", "medium", "large"]
    
    def change_model(self, model_name: str) -> bool:
        """
        切换Whisper模型
        
        Args:
            model_name: 模型名称
            
        Returns:
            是否切换成功
        """
        try:
            if model_name not in self.get_available_models():
                raise ValueError(f"不支持的模型: {model_name}")
            
            print(f"🔄 正在切换到模型: {model_name}")
            self.model = whisper.load_model(model_name)
            self.model_name = model_name
            print(f"✅ 模型切换成功: {model_name}")
            return True
            
        except Exception as e:
            print(f"❌ 模型切换失败: {e}")
            return False
