import asyncio
import aiohttp

from .serp import SerpClient
from .maps import MapsClient
from .scraper import scrape_website
from .utils import extract_domain, now_iso

MAX_CONCURRENT = 15

async def generate_leads(payload):
    serp = SerpClient(payload["serp_keys"], payload["config"]["serp_results"])
    maps = MapsClient(payload["serp_keys"])

    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT, ssl=False)
    timeout = aiohttp.ClientTimeout(total=40)

    leads = []
    seen_domains = set()

    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:

        for q in payload["queries"]:
            query_text = f"{q['query']} {q['location']}"

            serp_results = await serp.search(session, "google", query_text)
            maps_results = await maps.search(session, q["query"], q["location"])

            maps_lookup = {}
            for m in maps_results:
                dom = extract_domain(m.get("website"))
                if dom:
                    maps_lookup[dom] = m

            tasks = []

            for r in serp_results:
                url = r.get("link")
                domain = extract_domain(url)

                if not domain or domain in seen_domains:
                    continue

                seen_domains.add(domain)
                tasks.append(process_lead(session, r, maps_lookup.get(domain)))

            results = await asyncio.gather(*tasks)

            for lead in results:
                if lead:
                    leads.append(lead)

    return leads


async def process_lead(session, serp_item, maps_item):
    url = serp_item.get("link")
    domain = extract_domain(url)

    emails, phones = await scrape_website(session, url)

    return {
        "name": maps_item.get("title") if maps_item else serp_item.get("title"),
        "website": url,
        "domain": domain,
        "source": "maps" if maps_item else "serp",
        "email": emails[0] if emails else "",
        "phone": maps_item.get("phone") if maps_item else (phones[0] if phones else ""),
        "address": maps_item.get("address") if maps_item else "",
        "city": "",
        "state": "",
        "rating": maps_item.get("rating") if maps_item else None,
        "reviews": maps_item.get("reviews") if maps_item else None,
        "category": maps_item.get("type") if maps_item else "",
        "maps_url": maps_item.get("gps_coordinates") if maps_item else "",
        "place_id": maps_item.get("place_id") if maps_item else "",
        "scraped_at": now_iso(),
    }
