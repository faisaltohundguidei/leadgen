from urllib.parse import urlparse
from datetime import datetime, timezone

def extract_domain(url: str) -> str:
    if not url:
        return ""
    try:
        return urlparse(url).netloc.replace("www.", "").lower()
    except:
        return ""

def now_iso():
    return datetime.now(timezone.utc).isoformat()
