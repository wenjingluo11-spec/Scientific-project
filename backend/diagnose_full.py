#!/usr/bin/env python3
"""
直接测试 API 连接 - 完全模拟旧项目的 Rust 实现
不依赖 config.py，直接硬编码配置
"""

import asyncio
import httpx

# 使用旧项目的配置
OLD_PROJECT_CONFIG = {
    "base_url": "http://127.0.0.1:8045",  # 旧项目用这个，不带 /v1
    "api_key": "sk-691331534d4a403fbd2add1841357a8f",  # 旧项目的 key
    "model": "claude-haiku-4-5"
}

# 新项目的配置
NEW_PROJECT_CONFIG = {
    "base_url": "http://127.0.0.1:8045",  # 修正后不带 /v1
    "api_key": "sk-691331534d4a403fbd2add1841357a8f",  # 新项目的 key
    "model": "gemini-3-pro-high"
}

# 支持的模型列表
MODELS_TO_TEST = [
    "claude-haiku-4-5",
    "gemini-3-pro-high",
    "gemini-3-flash",
    "claude-sonnet-4-5"
]


async def test_direct_api(config: dict, config_name: str):
    """直接测试 API，完全模拟旧项目的请求方式"""
    
    base_url = config["base_url"].rstrip('/')
    url = f"{base_url}/v1/messages"
    
    headers = {
        "x-api-key": config["api_key"],
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    payload = {
        "model": config["model"],
        "max_tokens": 100,
        "messages": [{"role": "user", "content": "Hi"}]
    }
    
    print(f"\n{'='*60}")
    print(f"Testing: {config_name}")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"API Key: {config['api_key'][:15]}...")
    print(f"Model: {config['model']}")
    print(f"Headers: {headers}")
    print("-" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0, proxy=None) as client:
            response = await client.post(url, json=payload, headers=headers)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                text = data.get("content", [{}])[0].get("text", "")
                print(f"✅ SUCCESS! Response: {text}")
                return True
            else:
                print(f"❌ FAILED! Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False


async def test_all_models(base_url: str, api_key: str):
    """测试所有模型"""
    print(f"\n{'#'*60}")
    print(f"Testing all models with base_url: {base_url}")
    print(f"{'#'*60}")
    
    for model in MODELS_TO_TEST:
        config = {
            "base_url": base_url,
            "api_key": api_key,
            "model": model
        }
        success = await test_direct_api(config, f"Model: {model}")
        if success:
            print(f"\n🎉 Found working configuration!")
            print(f"   Base URL: {base_url}")
            print(f"   API Key: {api_key[:15]}...")
            print(f"   Model: {model}")
            return True
    
    return False


async def main():
    print("=" * 70)
    print("  API 连接诊断测试 - 模拟旧项目 Rust 实现")
    print("=" * 70)
    
    # 1. 先用旧项目配置测试
    print("\n\n📍 Step 1: 使用【旧项目】配置测试...")
    success = await test_direct_api(OLD_PROJECT_CONFIG, "旧项目配置")
    
    if not success:
        # 2. 用新项目配置测试
        print("\n\n📍 Step 2: 使用【新项目】配置测试...")
        success = await test_direct_api(NEW_PROJECT_CONFIG, "新项目配置")
    
    if not success:
        # 3. 尝试所有模型
        print("\n\n📍 Step 3: 尝试不同的模型...")
        for api_key in [OLD_PROJECT_CONFIG["api_key"], NEW_PROJECT_CONFIG["api_key"]]:
            if await test_all_models("http://127.0.0.1:8045", api_key):
                break
    
    print("\n\n" + "=" * 70)
    print("诊断完成!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
