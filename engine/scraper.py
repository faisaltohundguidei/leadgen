import re
import asyncio
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}")

def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    emails = list(set(EMAIL_RE.findall(text)))
    phones = list(set(PHONE_RE.findall(text)))

    return emails[:2], phones[:2]

async def scrape_website(session, url):
    try:
        async with session.get(url, timeout=12) as r:
            html = await r.text()
            return await asyncio.to_thread(parse_html, html)
    except:
        return [], []
