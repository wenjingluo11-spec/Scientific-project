
from anthropic import Anthropic
import os

# Candidate configurations
API_KEY = "sk-691331534d4a403fbd2add1841357a8f"

# Models to test (from LLM API.md)
MODELS = [
    "gemini-3-pro-high",
    "claude-sonnet-4-5",
    "claude-haiku-4-5" # The one currently failing
]

# Base URLs to test
BASE_URLS = [
    "http://127.0.0.1:8045/v1",
    "http://127.0.0.1:8045"
]

def test_config(model, base_url):
    print(f"\n--- Testing Model: {model} | URL: {base_url} ---")
    client = Anthropic(
        base_url=base_url,
        api_key=API_KEY
    )

    try:
        response = client.messages.create(
            model=model,
            max_tokens=100,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print("SUCCESS!")
        print(f"Response: {response.content[0].text}")
        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    success = False
    for url in BASE_URLS:
        for model in MODELS:
            if test_config(model, url):
                success = True
                break
        if success:
            break
