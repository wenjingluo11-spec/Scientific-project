
import httpx
import asyncio
import json
from typing import Optional, Dict, Any
from config import settings

class GeminiDeepResearchClient:
    """
    Client for Gemini Deep Research Agent
    Protocol: REST
    """
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        # Handle Base URL: default to Google's if not provided, or adapt from settings
        # If using local proxy, we assume it forwards correctly or follows Google structure
        
        # ------------------------------------------------------------------
        # Logic to deduce Base URL and API Key
        # ------------------------------------------------------------------
        
        # 1. Base URL
        if base_url:
            # User provided explicit base URL
            self.base_url = base_url.rstrip('/')
        elif "AIza" in (api_key or ""):
             # Heuristic: If API key looks like a Google Cloud key (starts with AIza), 
             # force use of official Google endpoint, bypassing any local proxy settings.
             self.base_url = "https://generativelanguage.googleapis.com"
        else:
            # Fallback to configuring from settings (likely local proxy)
            candidate = settings.ANTHROPIC_BASE_URL.rstrip('/')
            if candidate.endswith('/v1'):
                candidate = candidate[:-3]
            self.base_url = candidate

        # 2. API Key
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        
        self.headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        self.agent_name = "deep-research-pro-preview-12-2025"

    async def start_research(self, prompt: str) -> str:
        """
        Start a deep research task and return the interaction ID
        """
        url = f"{self.base_url}/v1beta/interactions"
        
        payload = {
            "input": prompt,
            "agent": self.agent_name,
            "background": True
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"Failed to start research: {response.text}")
            
            data = response.json()
            # Expecting data['name'] typically "interactions/ID" or just ID depending on proxy
            # Google API returns object with 'name' like 'interactions/12345...'
            if 'name' not in data:
                 raise Exception(f"Invalid response, missing 'name': {data}")
            
            return data['name'] # This should be the interaction ID (resource name)

    async def get_interaction_status(self, interaction_name: str) -> Dict[str, Any]:
        """
        Check status of interaction
        """
        # Ensure name is full path if needed, usually passed as returned
        # Google API expects GET https://.../v1beta/{name}
        
        # If name already starts with interactions/, just append to base
        # But URL construction needs care.
        # if interaction_name is "interactions/123", url is base + "/v1beta/interactions/123"
        # actually Google returns "interactions/123", endpoint is /v1beta/interactions/123? No.
        # Endpoint is GET .../v1beta/interactions/{id}
        
        # Let's handle the ID parsing
        interaction_id = interaction_name
        if "interactions/" in interaction_name:
            interaction_id = interaction_name.split("interactions/")[-1]
            
        url = f"{self.base_url}/v1beta/interactions/{interaction_id}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"Failed to get status: {response.text}")
            
            return response.json()

    async def run_research_task(self, prompt: str, poll_interval: int = 10) -> str:
        """
        High-level method: Start -> Poll -> Return Final Text
        """
        print(f"[DeepResearch] Starting task: {prompt[:50]}...")
        interaction_name = await self.start_research(prompt)
        print(f"[DeepResearch] Task started. Name: {interaction_name}")
        
        while True:
            await asyncio.sleep(poll_interval)
            status_data = await self.get_interaction_status(interaction_name)
            
            state = status_data.get('status', 'processing') # Google uses 'status': 'completed' / 'failed'
            
            if state == 'completed':
                # Extract output
                # output format: "outputs": [{"content": "...", "text": "..."}] 
                # SDK says outputs[-1].text
                outputs = status_data.get('outputs', [])
                if not outputs:
                    return ""
                
                # Try to find text
                last_output = outputs[-1]
                if 'text' in last_output:
                    return last_output['text']
                # Fallback check
                if 'content' in last_output:
                     return str(last_output['content'])
                return str(last_output)
                
            elif state == 'failed':
                error = status_data.get('error', 'Unknown Error')
                raise Exception(f"Deep Research Failed: {error}")
            
            else:
                # Still running
                # Maybe logic to print intermediate thoughts if available?
                print(f"[DeepResearch] Status: {state}...")

