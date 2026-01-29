
import requests

try:
    print("Requesting Competitors...")
    resp = requests.get("http://localhost:8001/api/v1/competitors/?topic_id=5")
    print(f"Status: {resp.status_code}")
    print(f"Body: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
