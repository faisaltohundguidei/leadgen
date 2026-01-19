import asyncio
import aiohttp
import itertools

from .serp import SerpClient
from .maps import MapsClient
from .google_search import GoogleSearchClient
from .scraper import scrape_website
from .utils import extract_domain, now_iso

MAX_CONCURRENT = 25

async def generate_leads(payload):
    serp_limit = 5
    serp = SerpClient(payload["serp_keys"], serp_limit)
    maps = MapsClient(payload["serp_keys"])
    google_direct = GoogleSearchClient()

    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT, ssl=False)
    timeout = aiohttp.ClientTimeout(total=120)

    leads = []
    seen_domains = set()
    if "existing_domains" in payload:
        seen_domains.update(payload["existing_domains"])

    # Prepare search tasks
    queries = payload.get("queries", [])
    locations = payload.get("locations", [])
    
    # Cross search: All queries x All locations
    search_combinations = list(itertools.product(queries, locations))
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        
        search_tasks = []
        for query, location in search_combinations:
            query_text = f"{query} {location}"
            search_tasks.append(serp.search(session, "google", query_text))
            search_tasks.append(maps.search(session, query, location))
            search_tasks.append(google_direct.search(session, query_text))

        # Execute all searches
        all_search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Flatten and organize results
        # Results valid only if they have a link
        maps_lookup = {}
        serp_candidates = []

        # Iterate through results. 
        # Structure: [Serp1, Maps1, Google1, Serp2, Maps2, Google2, ...]
        for i in range(0, len(all_search_results), 3):
            s_res = all_search_results[i]
            m_res = all_search_results[i+1] # Maps
            g_res = all_search_results[i+2] # Google Direct

            # Handle exceptions from gather
            if isinstance(s_res, Exception): s_res = []
            if isinstance(m_res, Exception): m_res = []
            if isinstance(g_res, Exception): g_res = []

            # Process Maps
            for m in m_res:
                dom = extract_domain(m.get("website"))
                if dom:
                    maps_lookup[dom] = m
            
            # Process Serp
            for r in s_res:
                serp_candidates.append(r)
                
            # Process Google Direct
            for g in g_res:
                serp_candidates.append(g)

        # Create scraping tasks for unique domains
        scrape_tasks = []
        for item in serp_candidates:
            url = item.get("link")
            domain = extract_domain(url)

            if not domain or domain in seen_domains:
                continue

            seen_domains.add(domain)
            scrape_tasks.append(process_lead(session, item, maps_lookup.get(domain)))

        # Run scraping
        if scrape_tasks:
            results = await asyncio.gather(*scrape_tasks, return_exceptions=True)
            for lead in results:
                if lead and not isinstance(lead, Exception):
                    leads.append(lead)

    return leads


async def process_lead(session, serp_item, maps_item):
    url = serp_item.get("link")
    base_domain = extract_domain(url)

    emails, phones, socials, title, desc = await scrape_website(session, url)

    # Prefer maps data, fallback to scraped data, then serp data
    name = maps_item.get("title") if maps_item else (title if title else serp_item.get("title"))
    
    return {
        "name": name,
        "website": url,
        "domain": base_domain,
        "source": "maps" if maps_item else serp_item.get("source", "serp"),
        "email": emails[0] if emails else "",
        "phone": maps_item.get("phone") if maps_item else (phones[0] if phones else ""),
        "mobile": phones[1] if len(phones) > 1 else "",
        "address": maps_item.get("address") if maps_item else "",
        "city": "", # Could extract from address if needed
        "state": "",
        "social_facebook": socials.get("facebook", ""),
        "social_instagram": socials.get("instagram", ""),
        "social_twitter": socials.get("twitter", ""),
        "social_linkedin": socials.get("linkedin", ""),
        "social_youtube": socials.get("youtube", ""),
        "description": desc or serp_item.get("snippet", ""),
        "rating": maps_item.get("rating") if maps_item else None,
        "reviews": maps_item.get("reviews") if maps_item else None,
        "category": maps_item.get("type") if maps_item else "",
        "maps_url": maps_item.get("gps_coordinates") if maps_item else "",
        "place_id": maps_item.get("place_id") if maps_item else "",
        "scraped_at": now_iso(),
    }
