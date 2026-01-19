import re
import urllib.parse
from bs4 import BeautifulSoup
import asyncio
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
]

class GoogleSearchClient:
    def __init__(self):
        pass

    async def search(self, session, query, num_results=10):
        encoded_query = urllib.parse.quote_plus(query)
        url = f"https://www.google.com/search?q={encoded_query}&num={num_results}&hl=en"
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        try:
            async with session.get(url, headers=headers, timeout=20) as r:
                if r.status != 200:
                    return []
                html = await r.text()
                return self.parse_results(html)
        except Exception as e:
            print(f"Google Search Error: {e}")
            return []

    def parse_results(self, html):
        soup = BeautifulSoup(html, "html.parser")
        results = []
        
        # This selector targets the main container for each search result
        for g in soup.select("div.g"):
            title_node = g.select_one("h3")
            link_node = g.select_one("a")
            snippet_node = g.select_one("div.VwiC3b") or g.select_one("div.IsZvec")
            
            if title_node and link_node:
                link = link_node["href"]
                # Filter out google related links if any leak through
                if link.startswith("/"):
                    continue
                    
                results.append({
                    "title": title_node.get_text(),
                    "link": link,
                    "snippet": snippet_node.get_text() if snippet_node else "",
                    "source": "google_direct"
                })
                
        return results
