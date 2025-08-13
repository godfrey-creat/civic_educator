import os
import requests
from typing import Optional, Dict, Any

class SerpAPIClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SERPAPI_KEY")
        self.base_url = "https://serpapi.com/search"

    def available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str) -> Optional[Dict[str, Any]]:
        if not self.available():
            return None
        params = {
            "engine": "google",
            "q": query,
            "api_key": self.api_key,
        }
        resp = requests.get(self.base_url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        org = data.get("organic_results") or []
        if not org:
            return None
        top = org[0]
        return {
            "title": top.get("title"),
            "snippet": top.get("snippet"),
            "link": top.get("link"),
        }
