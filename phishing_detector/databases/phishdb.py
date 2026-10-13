"""PhishTank and OpenPhish database integrations"""

import aiohttp
import hashlib
from typing import Dict, Any

from .base import BaseDatabase


class PhishTankDatabase(BaseDatabase):
    """PhishTank database lookup (requires API key for production)"""
    
    def __init__(self, api_key: str = None):
        super().__init__("PhishTank")
        self.api_key = api_key
        self.base_url = "https://data.phishtank.com/data"
    
    async def lookup(self, input_str: str) -> Dict[str, Any]:
        """
        Check URL against PhishTank database
        Note: Free tier requires downloading the entire database
        """
        if not self.api_key:
            # For demo, return not found
            return {"found": False}
        
        # In production, you'd download and parse the CSV
        # or use their API if available
        return {"found": False}


class OpenPhishDatabase(BaseDatabase):
    """OpenPhish feed integration"""
    
    def __init__(self):
        super().__init__("OpenPhish")
        self.feed_url = "https://openphish.com/feed.txt"
        self.phishing_urls = set()
        self.last_update = 0
    
    async def _update_feed(self):
        """Update phishing URLs from feed"""
        import time
        current_time = time.time()
        
        # Update every hour
        if current_time - self.last_update < 3600:
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.feed_url, timeout=10) as response:
                    if response.status == 200:
                        text = await response.text()
                        self.phishing_urls = set(text.strip().split('\n'))
                        self.last_update = current_time
        except Exception:
            pass
    
    async def lookup(self, input_str: str) -> Dict[str, Any]:
        """Check if URL is in OpenPhish feed"""
        await self._update_feed()
        
        # Normalize URL for comparison
        normalized = input_str.lower().strip()
        
        if normalized in self.phishing_urls:
            return {
                "found": True,
                "threat_type": "phishing",
                "confidence": 0.85,
                "details": "URL found in OpenPhish phishing feed"
            }
        
        return {"found": False}


class GoogleSafeBrowsing(BaseDatabase):
    """Google Safe Browsing API"""
    
    def __init__(self, api_key: str = None):
        super().__init__("Google Safe Browsing")
        from core.config import get_config
        config = get_config()
        self.api_key = api_key or config.api.googlesafe_api_key
        self.base_url = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
    
    async def lookup(self, input_str: str) -> Dict[str, Any]:
        """Check URL against Google Safe Browsing"""
        if not self.api_key:
            return {"found": False}
        
        payload = {
            "client": {
                "clientId": "phishing-detector",
                "clientVersion": "1.0.0"
            },
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": input_str}]
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}?key={self.api_key}",
                json=payload,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('matches'):
                        match = data['matches'][0]
                        return {
                            "found": True,
                            "threat_type": match.get('threatType', 'malicious').lower(),
                            "confidence": 0.95,
                            "details": f"Flagged by Google Safe Browsing: {match.get('threatType')}"
                        }
        
        return {"found": False}