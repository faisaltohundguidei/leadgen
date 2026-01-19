import itertools

class MapsClient:
    def __init__(self, api_keys):
        self.keys = itertools.cycle(api_keys)

    async def search(self, session, query, location):
        params = {
            "engine": "google_maps",
            "q": query,
            "location": location,
            "api_key": next(self.keys),
        }

        try:
            async with session.get("https://serpapi.com/search", params=params, timeout=20) as r:
                data = await r.json()
                return data.get("local_results", [])
        except:
            return []
