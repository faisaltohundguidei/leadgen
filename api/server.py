from fastapi import FastAPI, HTTPException
from engine.lead_generator import generate_leads
import secrets

app = FastAPI(title="LeadGen API")

API_KEYS = set()

@app.post("/generate-api-key")
def generate_api_key():
    key = "lg_" + secrets.token_hex(20)
    API_KEYS.add(key)
    return {"api_key": key}

@app.post("/generate-leads")
async def generate(payload: dict, x_api_key: str = ""):
    if x_api_key not in API_KEYS:
        raise HTTPException(401, "Invalid API key")

    leads = await generate_leads(payload)

    return {
        "status": "success",
        "count": len(leads),
        "leads": leads
    }
