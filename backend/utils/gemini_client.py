
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
        
        print(f"[GeminiClient] Initialized with Base URL: {self.base_url}", flush=True)
        print(f"[GeminiClient] API Key Prefix: {str(self.api_key)[:4]}...", flush=True)
        if "googleapis.com" in self.base_url:
            print("[GeminiClient] MODE: DIRECT (Bypassing Proxy)", flush=True)
        else:
            print("[GeminiClient] MODE: PROXY (Forwarding to local gateway)", flush=True)
        
        self.headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        self.agent_name = "deep-research-pro-preview-12-2025"
        # Determine if we should trust system environment proxies
        self.trust_env = False if "googleapis.com" in self.base_url else True

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
        
        print(f"[GeminiClient] POSTing to: {url}", flush=True)
        
        async with httpx.AsyncClient(timeout=30.0, trust_env=self.trust_env) as client:
            response = await client.post(url, headers=self.headers, json=payload)
            
            if response.status_code != 200:
                raise Exception(f"Failed to start research: {response.text}")
            
            data = response.json()
            # Expecting data['name'] typically "interactions/ID" or just ID depending on proxy
            # Google API returns object with 'name' like 'interactions/12345...'
            if 'name' not in data and 'id' not in data:
                 raise Exception(f"Invalid response, missing identity field: {data}")
            
            return data.get('name') or data.get('id')

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
            
        # For some proxies, the URL structure might be different, but we'll try the standard Google one first
        url = f"{self.base_url}/v1beta/interactions/{interaction_id}"
        print(f"[GeminiClient] GEt-Polling: {url}", flush=True)
        
        async with httpx.AsyncClient(timeout=30.0, trust_env=self.trust_env) as client:
            response = await client.get(url, headers=self.headers)
            
            if response.status_code != 200:
                raise Exception(f"Failed to get status: {response.text}")
            
            return response.json()

    async def run_research_task(self, prompt: str, poll_interval: int = 10) -> str:
        """
        High-level method: Start -> Poll -> Return Final Text
        """
        print(f"[DeepResearch] Starting task: {prompt[:50]}...", flush=True)
        interaction_name = await self.start_research(prompt)
        print(f"[DeepResearch] Task started. Name: {interaction_name}", flush=True)
        
        while True:
            await asyncio.sleep(poll_interval)
            status_data = await self.get_interaction_status(interaction_name)
            
            # Try common state fields
            state = (status_data.get('status') or status_data.get('state') or 'processing').lower()
            
            if state in ('completed', 'succeeded', 'done'):
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
                print(f"[DeepResearch] Status: {state}...", flush=True)

    async def generate_simple_content(self, prompt: str, model_name: str = "gemini-flash-latest") -> str:
        """
        Invoke standard generateContent API directly. 
        Pass key in URL for maximum compatibility.
        """
        clean_base = self.base_url.replace("/v1beta", "").replace("/v1", "")
        
        endpoints = [
            f"{clean_base}/v1/models/{model_name}:generateContent?key={self.api_key}",
            f"{clean_base}/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        ]
        
        last_error = ""
        for url in endpoints:
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "response_mime_type": "application/json" if "JSON" in prompt.upper() else "text/plain"
                }
            }
            
            print(f"[GeminiClient] Trying Direct Call (with URL key)...", flush=True)
            
            try:
                # We don't need the header key if we pass it in the URL, but keeping Content-Type
                headers = {"Content-Type": "application/json"}
                async with httpx.AsyncClient(timeout=60.0, trust_env=self.trust_env) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        return data['candidates'][0]['content']['parts'][0]['text']
                    else:
                        last_error = response.text
                        continue
            except Exception as e:
                last_error = str(e)
                continue
                
        raise Exception(f"Failed to generate content after trying multiple endpoints. Last error: {last_error}")
