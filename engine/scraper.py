import re
import asyncio
from bs4 import BeautifulSoup

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
# Strict but common patterns: (123) 456-7890, 123-456-7890, +1 123 456 7890, 123.456.7890
PHONE_RE = re.compile(r'(?:\+?\d{1,3}[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}')

SOCIAL_PLATFORMS = {
    "facebook": re.compile(r"facebook\.com/[a-zA-Z0-9.]+"),
    "instagram": re.compile(r"instagram\.com/[a-zA-Z0-9_.]+"),
    "linkedin": re.compile(r"linkedin\.com/(?:in|company)/[a-zA-Z0-9_-]+"),
    "twitter": re.compile(r"twitter\.com/[a-zA-Z0-9_]+"),
    "youtube": re.compile(r"youtube\.com/(?:channel|user|c)/[a-zA-Z0-9_-]+"),
}

def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    emails = list(set(EMAIL_RE.findall(text)))
    
    # Filter phones to ensure they have enough digits and aren't just dates
    raw_phones = PHONE_RE.findall(text)
    phones = []
    for p in raw_phones:
        # If regex contained groups, p is tuple. My simplified regex has no capturing groups (except implicit full match if findall used without groups? No, findall returns full match if no groups).
        # But wait, my previous regex MIGHT have had groups? No, I am replacing it.
        # This new regex has NO capturing groups (only non-capturing (?:...)).
        
        # Clean the phone number
        clean_p = p.strip()
        # strictly digits check length > 9 
        digits = re.sub(r'\D', '', clean_p)
        if len(digits) >= 10:
            phones.append(clean_p)
            
    phones = list(set(phones))
    
    socials = {}
    
    socials = {}
    for platform, pattern in SOCIAL_PLATFORMS.items():
        # Search in hrefs primarily
        links = [a['href'] for a in soup.find_all('a', href=True) if pattern.search(a['href'])]
        if links:
            socials[platform] = links[0]

    title = soup.title.string if soup.title else ""
    meta_desc = soup.find("meta", attrs={"name": "description"})
    description = meta_desc["content"] if meta_desc else ""

    return emails[:5], phones[:5], socials, title, description

async def scrape_website(session, url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with session.get(url, headers=headers, timeout=15) as r:
            html = await r.text()
            return await asyncio.to_thread(parse_html, html)
    except:
        return [], [], {}, "", ""
