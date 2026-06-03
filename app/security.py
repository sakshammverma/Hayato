import hmac
import hashlib # provides SHA256 hashing algorithm
from fastapi import Request, HTTPException, Depends
import os
from dotenv import load_dotenv

load_dotenv()
async def verify_signature(request:Request):
    secret= os.getenv("GITHUB_WEBHOOK_SECRET")  
    
    if not secret:
        raise HTTPException(status_code=401, detail="Missing webhook secret")

    signature_head = request.headers.get("x-hub-signature-256")  

    if not signature_head:
        raise HTTPException(status_code=401, detail="Missing signature")
    
    body = await request.body()

    expected = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    expected_header = f"sha256={expected}"

    if not hmac.compare_digest(signature_head, expected_header):    
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    print(f"Header signature:   {signature_head}")
    print(f"Computed signature: {expected_header}")
    print(f"Body received: {body[:100]}")  # first 100 bytes
