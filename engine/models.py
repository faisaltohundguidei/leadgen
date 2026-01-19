from dataclasses import dataclass, field
from typing import List, Dict, Set

@dataclass
class LeadGenConfig:
    scrape_paths: List[str]
    max_concurrent_http: int
    headers: Dict[str, str]
    serp_engines: List[Dict[str, str]]

@dataclass
class LeadRequest:
    queries: List[str]
    locations: List[str]
    existing_domains: Set[str] = field(default_factory=set)
