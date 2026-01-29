
import requests

url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer e934ab82-67ea-41f8-9d8d-b1aff85e7f74"
}
data = {
    "model": "ep-20250416114912-nsdxw",
    "messages": [
        {"role": "user", "content": "Hello"}
    ]
}

print("Testing raw request...")
try:
    resp = requests.post(url, headers=headers, json=data, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
