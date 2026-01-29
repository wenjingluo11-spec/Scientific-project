#!/usr/bin/env python3
"""
最小化测试 - 排除所有可能的干扰因素
"""

import asyncio
import httpx
import os

# 清除可能的代理环境变量
for key in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']:
    os.environ.pop(key, None)
os.environ['NO_PROXY'] = '*'

async def test_minimal():
    """使用与 curl 完全相同的请求"""
    
    url = "http://127.0.0.1:8045/v1/messages"
    
    headers = {
        "x-api-key": "sk-691331534d4a403fbd2add1841357a8f",
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    payload = {
        "model": "claude-haiku-4-5",
        "max_tokens": 50,
        "messages": [{"role": "user", "content": "Hi"}]
    }
    
    print(f"Testing with httpx...")
    print(f"URL: {url}")
    print(f"Payload: {payload}")
    
    # 方法1: 使用 AsyncClient
    print("\n--- Method 1: AsyncClient ---")
    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            verify=False,  # 禁用 SSL 验证
            follow_redirects=True
        ) as client:
            response = await client.post(url, json=payload, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500] if response.text else '(empty)'}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 方法2: 使用同步 Client
    print("\n--- Method 2: Sync Client ---")
    try:
        with httpx.Client(
            timeout=30.0,
            verify=False,
            follow_redirects=True
        ) as client:
            response = client.post(url, json=payload, headers=headers)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500] if response.text else '(empty)'}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 方法3: 使用 requests 库
    print("\n--- Method 3: requests library ---")
    try:
        import requests
        response = requests.post(url, json=payload, headers=headers, timeout=30, verify=False)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500] if response.text else '(empty)'}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')
    asyncio.run(test_minimal())
