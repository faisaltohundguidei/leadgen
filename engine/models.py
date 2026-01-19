from dataclasses import dataclass
from typing import List, Dict, Set

@dataclass
class QueryConfig:
    query: str
    location: str

@dataclass
class LeadGenConfig:
    serp_results: int
    scrape_paths: List[str]
    max_concurrent_http: int
    headers: Dict[str, str]
    serp_engines: List[Dict[str, str]]

@dataclass
class LeadRequest:
    queries: List[QueryConfig]
    existing_domains: Set[str]
