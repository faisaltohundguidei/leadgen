from fastapi import FastAPI, HTTPException, Body
from engine.lead_generator import generate_leads
import secrets
import csv
import os
import aiofiles
from datetime import datetime, timedelta, timezone

app = FastAPI(title="LeadGen API")

KEYS_FILE = "users.csv"
API_KEY_VALIDITY_MINUTES = 10

def load_keys():
    keys = {}
    if not os.path.exists(KEYS_FILE):
        return keys
    
    with open(KEYS_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            keys[row["api_key"]] = {
                "email": row["email"],
                "created_at": datetime.fromisoformat(row["created_at"])
            }
    return keys

def count_user_keys(email):
    count = 0
    if not os.path.exists(KEYS_FILE):
        return 0
    with open(KEYS_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["email"] == email:
                count += 1
    return count

@app.post("/generate-api-key")
async def generate_api_key(email: str = Body(..., embed=True)):
    if not email:
        raise HTTPException(400, "Email is required")

    key = "lg_" + secrets.token_hex(20)
    created_at = datetime.now(timezone.utc)
    
    # Check if file exists to write header
    file_exists = os.path.exists(KEYS_FILE)
    
    async with aiofiles.open(KEYS_FILE, mode="a", newline="") as f:
        # We can't easily use csv.writer with aiofiles in async perfectly without blocking, 
        # but for this scale string manipulation is fine to avoid blocking too much or complexity.
        if not file_exists:
            await f.write("email,api_key,created_at\n")
        
        await f.write(f"{email},{key},{created_at.isoformat()}\n")

    user_key_count = count_user_keys(email)

    return {
        "api_key": key, 
        "validity": f"{API_KEY_VALIDITY_MINUTES} minutes",
        "keys_generated_count": user_key_count
    }

@app.post("/generate-leads")
async def generate(payload: dict, x_api_key: str = ""):
    keys = load_keys() # Load fresh
    
    if x_api_key not in keys:
        raise HTTPException(401, "Invalid API key")
    
    key_data = keys[x_api_key]
    created_at = key_data["created_at"]
    
    # Check expiry
    if datetime.now(timezone.utc) > created_at + timedelta(minutes=API_KEY_VALIDITY_MINUTES):
        raise HTTPException(401, "API key has expired")

    leads = await generate_leads(payload)

    return {
        "status": "success",
        "count": len(leads),
        "leads": leads
    }
