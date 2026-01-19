import itertools

class SerpClient:
    def __init__(self, api_keys, results):
        self.keys = itertools.cycle(api_keys)
        self.results = results

    async def search(self, session, engine, query):
        params = {
            "engine": engine,
            "q": query,
            "api_key": next(self.keys),
            "num": self.results,
            "hl": "en",
            "gl": "us",
        }

        try:
            async with session.get("https://serpapi.com/search", params=params, timeout=20) as r:
                data = await r.json()
                return data.get("organic_results", [])
        except:
            return []
