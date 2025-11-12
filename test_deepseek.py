#!/usr/bin/env python3
"""
测试DeepSeek API连接
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

def test_deepseek():
    """测试DeepSeek API"""
    load_dotenv()
    
    api_key = os.getenv('DEEPSEEK_API_KEY')
    
    if not api_key or api_key == "你的DeepSeek_API_Key":
        print("❌ 请先设置DEEPSEEK_API_KEY")
        print("📝 获取API Key:")
        print("   1. 访问 https://platform.deepseek.com/")
        print("   2. 注册/登录账号")
        print("   3. 创建API Key")
        print("   4. 在.env文件中设置DEEPSEEK_API_KEY")
        return False
    
    try:
        print("🧪 测试DeepSeek API连接...")
        
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{
                "role": "user",
                "content": "请回复：DeepSeek API连接成功！"
            }],
            max_tokens=50
        )
        
        result = response.choices[0].message.content
        print(f"✅ DeepSeek API连接成功")
        print(f"📝 响应: {result}")
        return True
        
    except Exception as e:
        print(f"❌ DeepSeek API连接失败: {e}")
        return False

if __name__ == '__main__':
    success = test_deepseek()
    if success:
        print("\n🎉 可以启动DeepSeek版本的Bot了！")
        print("📱 启动命令: python bot_deepseek.py")
    else:
        print("\n⚠️ 请先配置DeepSeek API Key")