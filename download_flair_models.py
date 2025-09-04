#!/usr/bin/env python3
"""下载 Flair 模型"""

import os
import sys

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def download_models():
    """下载 Flair 模型"""
    print("🚀 开始下载 Flair 模型...")
    print("=" * 50)
    
    try:
        from flair.models import SequenceTagger
        
        models = [
            'flair/ner-english',
            'flair/ner-english-fast'
        ]
        
        for model_name in models:
            print(f"📥 正在下载模型: {model_name}")
            try:
                tagger = SequenceTagger.load(model_name)
                print(f"✅ {model_name} 下载成功！")
                print(f"   模型路径: {tagger.model_card.model_name}")
            except Exception as e:
                print(f"❌ {model_name} 下载失败: {e}")
                print(f"   错误类型: {type(e).__name__}")
            
            print("-" * 30)
        
        # 检查模型目录
        flair_dir = os.path.expanduser("~/.flair/models")
        if os.path.exists(flair_dir):
            print(f"📁 Flair 模型目录: {flair_dir}")
            for root, dirs, files in os.walk(flair_dir):
                level = root.replace(flair_dir, '').count(os.sep)
                indent = ' ' * 2 * level
                print(f"{indent}{os.path.basename(root)}/")
                subindent = ' ' * 2 * (level + 1)
                for file in files:
                    print(f"{subindent}{file}")
        else:
            print(f"❌ Flair 模型目录不存在: {flair_dir}")
            
    except ImportError as e:
        print(f"❌ 无法导入 Flair: {e}")
        print("请确保已安装 Flair: pip install flair")
    except Exception as e:
        print(f"❌ 下载过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    download_models()
    print("\n🎉 模型下载完成！")
