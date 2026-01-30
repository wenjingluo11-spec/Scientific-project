
import requests
import json

url = "http://127.0.0.1:8001/api/v1/topics/ai-discover"
data = {
    "research_field": "Artificial Intelligence",
    "keywords": ["Large Language Models"],
    "num_suggestions": 1
}
try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(response.text)
except Exception as e:
    print(e)
