#!/usr/bin/env python3
"""
真正的API测试脚本 - 使用真实音频文件测试
"""

import urllib.request
import urllib.parse
import json
import time
import os

BASE_URL = "http://localhost:3000"
TEST_AUDIO_FILE = "test_audio/test_audio_1.m4a"

def test_health():
    """测试健康检查端点"""
    print("🔍 测试健康检查...")
    try:
        with urllib.request.urlopen(f"{BASE_URL}/health") as response:
            status_code = response.getcode()
            data = json.loads(response.read().decode())
            print(f"状态码: {status_code}")
            print(f"响应: {data}")
            print("✅ 健康检查通过\n")
            return True
    except Exception as e:
        print(f"❌ 健康检查失败: {e}\n")
        return False

def test_root():
    """测试根端点"""
    print("🏠 测试根端点...")
    try:
        with urllib.request.urlopen(f"{BASE_URL}/") as response:
            status_code = response.getcode()
            data = json.loads(response.read().decode())
            print(f"状态码: {status_code}")
            print(f"响应: {data}")
            print("✅ 根端点测试通过\n")
            return True
    except Exception as e:
        print(f"❌ 根端点测试失败: {e}\n")
        return False

def test_audio_endpoints():
    """测试音频相关端点"""
    print("🎵 测试音频端点...")
    
    # 测试支持的格式
    try:
        with urllib.request.urlopen(f"{BASE_URL}/api/audio/supported-formats") as response:
            status_code = response.getcode()
            data = json.loads(response.read().decode())
            print(f"  📋 支持的格式: {status_code} - {data}")
    except Exception as e:
        print(f"  ❌ 支持的格式测试失败: {e}")
    
    # 测试模型信息
    try:
        with urllib.request.urlopen(f"{BASE_URL}/api/audio/models") as response:
            status_code = response.getcode()
            data = json.loads(response.read().decode())
            print(f"  🤖 模型信息: {status_code} - {data}")
    except Exception as e:
        print(f"  ❌ 模型信息测试失败: {e}")
    
    print("✅ 音频端点测试完成\n")

def test_transcribe_with_real_audio():
    """使用真实音频文件测试音频转换端点"""
    print("📤 测试真实音频文件转换...")
    
    # 检查测试音频文件是否存在
    if not os.path.exists(TEST_AUDIO_FILE):
        print(f"❌ 测试音频文件不存在: {TEST_AUDIO_FILE}")
        print("请确保 test_audio/test_audio_1.m4a 文件存在")
        return False
    
    try:
        # 开始总计时
        total_start_time = time.time()
        
        # 1. 文件读取时间
        file_read_start = time.time()
        with open(TEST_AUDIO_FILE, 'rb') as f:
            audio_content = f.read()
        file_read_time = time.time() - file_read_start
        
        print(f"📁 读取音频文件: {TEST_AUDIO_FILE}")
        print(f"📊 文件大小: {len(audio_content)} 字节")
        print(f"⏱️  文件读取耗时: {file_read_time:.3f}秒")
        
        # 2. 构建请求数据时间
        request_build_start = time.time()
        
        # 创建multipart/form-data请求
        boundary = '----WebKitFormBoundary' + str(int(time.time() * 1000))
        headers = {
            'Content-Type': f'multipart/form-data; boundary={boundary}'
        }
        
        # 构建multipart数据
        data = b''
        data += f'--{boundary}\r\n'.encode()
        data += f'Content-Disposition: form-data; name="audio_file"; filename="test_audio_1.m4a"\r\n'.encode()
        data += b'Content-Type: audio/m4a\r\n\r\n'  # 使用更准确的MIME类型
        data += audio_content
        data += f'\r\n--{boundary}--\r\n'.encode()
        
        request_build_time = time.time() - request_build_start
        print(f"⏱️  请求构建耗时: {request_build_time:.3f}秒")
        
        print("🚀 发送音频转换请求...")
        
        # 3. 网络传输时间
        network_start = time.time()
        req = urllib.request.Request(
            f"{BASE_URL}/api/audio/transcribe",
            data=data,
            headers=headers
        )
        
        with urllib.request.urlopen(req) as response:
            network_time = time.time() - network_start
            
            # 4. 响应解析时间
            parse_start = time.time()
            status_code = response.getcode()
            response_data = json.loads(response.read().decode())
            parse_time = time.time() - parse_start
            
            # 总耗时
            total_time = time.time() - total_start_time
            
            print(f"  🎵 音频转换成功: {status_code}")
            print(f"  📝 转换结果: {response_data['transcription']}")
            print(f"  🌍 识别语言: {response_data['language']}")
            print(f"  🤖 使用模型: {response_data['model']}")
            print(f"  📊 音频分段数: {len(response_data['segments'])}")
            
            # 详细时间分析
            print(f"\n⏱️  **详细时间分析**")
            print(f"  📁 文件读取: {file_read_time:.3f}秒 ({file_read_time/total_time*100:.1f}%)")
            print(f"  🔧 请求构建: {request_build_time:.3f}秒 ({request_build_time/total_time*100:.1f}%)")
            print(f"  🌐 网络传输: {network_time:.3f}秒 ({network_time/total_time*100:.1f}%)")
            print(f"  📋 响应解析: {parse_time:.3f}秒 ({parse_time/total_time*100:.1f}%)")
            print(f"  🎯 总耗时: {total_time:.3f}秒")
            
            # 计算音频处理时间（网络时间 - 请求构建时间）
            audio_processing_time = network_time - request_build_time
            print(f"  🎵 音频处理(服务器): {audio_processing_time:.3f}秒 ({audio_processing_time/total_time*100:.1f}%)")
            
            # Latency优化建议
            print(f"\n💡 **Latency优化建议**")
            if audio_processing_time > total_time * 0.7:
                print(f"  🚀 主要瓶颈在音频处理，建议:")
                print(f"     - 使用更小的Whisper模型 (tiny/base)")
                print(f"     - 优化音频文件大小")
                print(f"     - 考虑异步处理")
            elif network_time > total_time * 0.5:
                print(f"  🌐 主要瓶颈在网络传输，建议:")
                print(f"     - 压缩音频文件")
                print(f"     - 使用更快的网络")
                print(f"     - 考虑本地部署")
            else:
                print(f"  ✅ 性能表现良好")
            
            print("✅ 真实音频转换测试通过\n")
            return True
            
    except urllib.error.HTTPError as e:
        print(f"  ❌ 音频转换HTTP错误: {e.code}")
        error_body = e.read().decode()
        print(f"  错误详情: {error_body}")
        return False
    except Exception as e:
        print(f"  ❌ 音频转换测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🧪 开始真正的API测试...\n")
    
    # 检查服务器是否运行
    if not test_health():
        print("❌ 服务器未运行，请先启动服务器: python run.py")
        return
    
    # 测试其他端点
    test_root()
    test_audio_endpoints()
    
    # 测试真实音频转换
    if test_transcribe_with_real_audio():
        print("🎉 所有测试通过！")
    else:
        print("❌ 音频转换测试失败")
    
    print("\n💡 提示:")
    print("- 所有测试都发送了真实的HTTP请求")
    print(f"- 使用了真实音频文件: {TEST_AUDIO_FILE}")
    print("- 测试了完整的音频转换流程")
    print("- 检查了所有主要端点")
    print("- 提供了详细的latency分析和优化建议")

if __name__ == "__main__":
    main()
