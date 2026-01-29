
import requests
import json
import os

API_KEY = "sk-691331534d4a403fbd2add1841357a8f"
MODEL = "claude-haiku-4-5"

urls_to_test = [
    "http://127.0.0.1:8045/v1/messages",
]

headers = {
    "x-api-key": API_KEY,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

data = {
    "model": MODEL,
    "max_tokens": 1024,
    "messages": [{"role": "user", "content": "Hello"}]
}

for url in urls_to_test:
    print(f"--- Testing {url} ---")
    try:
        resp = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status Code: {resp.status_code}")
        print(f"Headers: {resp.headers}")
        print(f"Content: {resp.text[:500]}")
    except Exception as e:
        print(f"Exception: {e}")
