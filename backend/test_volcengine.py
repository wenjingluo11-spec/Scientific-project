
import asyncio
import os
import sys

# Add backend to sys.path
sys.path.append(os.getcwd())

from utils.anthropic_client import AnthropicClient
from config import settings

async def test_volcengine():
    print(f"Testing Volcengine Connection...")
    print(f"Base URL: {settings.ANTHROPIC_BASE_URL}")
    print(f"Model: {settings.DEFAULT_MODEL}")
    
    client = AnthropicClient()
    
    try:
        response = await client.create_message(
            role="topic_discovery_expert",
            context="Testing Volcengine Integration",
            task="Please return a simple JSON: {\"status\": \"success\"}"
        )
        print("\n--- Response Received ---")
        print(response)
    except Exception as e:
        print(f"\nFAIL: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_volcengine())
