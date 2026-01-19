from firebase_functions import https_fn
from flask import jsonify
import asyncio

from engine.lead_generator import generate_leads
from engine.models import LeadRequest, LeadGenConfig, QueryConfig
from engine.serp import SerpClient
from storage.google_sheets import GoogleSheetsStorage

@https_fn.on_request(timeout_sec=540)
def cas_lead_generator(req):
    try:
        storage = GoogleSheetsStorage()
        existing = storage.load_existing_domains()

        request = LeadRequest(
            queries=storage.load_queries(),
            existing_domains=existing,
        )

        config = LeadGenConfig(
            serp_results=5,
            scrape_paths=["", "/contact", "/about"],
            headers={"User-Agent": "Mozilla/5.0"},
            serp_engines=[
                {"id": "google", "label": "Google"},
                {"id": "bing", "label": "Bing"},
            ],
        )

        serp_client = SerpClient(
            api_keys=req.json.get("serp_keys"),
            results_per_query=config.serp_results,
        )

        rows = asyncio.run(generate_leads(request, config, serp_client))
        storage.save_leads(rows)

        return jsonify({"status": "success", "leads_added": len(rows)})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
