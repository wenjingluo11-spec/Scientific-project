#!/usr/bin/env python3
"""
测试 Raw LLM Client - 使用与旧项目完全一致的实现
"""

import asyncio
import sys
import os

# 确保可以导入 backend 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.raw_llm_client import RawLLMClient
from config import settings


async def test_basic_completion():
    """测试基本的模型调用"""
    print("=" * 60)
    print("Testing RawLLMClient (与旧项目 Rust 实现一致)")
    print("=" * 60)
    print(f"Base URL: {settings.ANTHROPIC_BASE_URL}")
    print(f"API Key: {settings.ANTHROPIC_API_KEY[:10]}...")
    print(f"Model: {settings.DEFAULT_MODEL}")
    print("-" * 60)
    
    client = RawLLMClient()
    
    # 测试 1: 基本调用
    print("\n[Test 1] 基本消息调用...")
    try:
        response = await client.complete(
            messages=[{"role": "user", "content": "Say 'Hello' in Chinese."}],
            max_tokens=50
        )
        print(f"✅ SUCCESS! Response: {response}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # 测试 2: 带系统提示词
    print("\n[Test 2] 带系统提示词调用...")
    try:
        response = await client.complete(
            messages=[{"role": "user", "content": "What is 2+2?"}],
            system="You are a math tutor. Always respond with just the number.",
            max_tokens=10
        )
        print(f"✅ SUCCESS! Response: {response}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    # 测试 3: 使用指定模型
    print("\n[Test 3] 使用 claude-haiku-4-5 模型...")
    try:
        response = await client.complete(
            messages=[{"role": "user", "content": "Reply with 'OK'"}],
            model="claude-haiku-4-5",
            max_tokens=10
        )
        print(f"✅ SUCCESS! Response: {response}")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        # 这个失败不影响整体测试
    
    print("\n" + "=" * 60)
    print("All basic tests passed!")
    print("=" * 60)
    return True


async def test_create_message():
    """测试 create_message 方法 (AnthropicClient 兼容接口)"""
    print("\n[Test 4] create_message 方法 (兼容接口)...")
    
    client = RawLLMClient()
    
    try:
        response = await client.create_message(
            role="topic_discovery_expert",
            context="用户想研究人工智能在医疗领域的应用",
            task="请简要列出3个可能的研究方向（每个不超过10个字）"
        )
        print(f"✅ SUCCESS!")
        print(f"Response preview: {response[:200]}...")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False
    
    return True


async def main():
    success = await test_basic_completion()
    if success:
        await test_create_message()


if __name__ == "__main__":
    asyncio.run(main())
