
import requests
from config import settings

url = "http://127.0.0.1:8045/v1beta/interactions"
api_key = settings.ANTHROPIC_API_KEY
headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": api_key
}
payload = {
    "input": "Test request for deep research availability",
    "agent": "deep-research-pro-preview-12-2025",
    "background": True
}

print(f"Connecting to: {url} with key: {api_key[:5]}...")

try:
    response = requests.post(url, headers=headers, json=payload, timeout=10)
    print(f"Status Code: {response.status_code}")
    print("Headers:", response.headers)
    print("Response Body:", response.text)
    
    if response.status_code == 200:
        print("\n✅ Deep Research Endpoint is accessible!")
    elif response.status_code == 404:
        print("\n❌ 404 Not Found: The proxy/server does not support /v1beta/interactions endpoint.")
    else:
        print(f"\n❌ Request failed: {response.status_code}")
        
except Exception as e:
    print(f"\n❌ Connection Error: {e}")
