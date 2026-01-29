
from anthropic import Anthropic
import os

# Configuration matching your new setup
BASE_URL = "http://127.0.0.1:8045/v1"
API_KEY = "sk-f3cdd22cdf5340c78eca9cc4f9b6258c"
MODEL = "claude-haiku-4-5"

def test_connection():
    print(f"Testing connection to {BASE_URL}...")

    client = Anthropic(
        base_url=BASE_URL,
        api_key=API_KEY
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": "Hello, are you working?"}]
        )

        print("\nSuccess! Response:")
        print(response.content[0].text)

    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_connection()
