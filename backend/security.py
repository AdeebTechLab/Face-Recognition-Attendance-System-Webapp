import os
import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

DEV_DEFAULT_KEY = "dev-biometric-secret-key-2026"

if not os.getenv("BACKEND_API_KEY"):
    print("WARNING: BACKEND_API_KEY is not set; using the insecure development key. Set it in production.")

def get_api_key(api_key: str = Security(api_key_header)):
    expected_key = os.getenv("BACKEND_API_KEY", DEV_DEFAULT_KEY)
    if not api_key or not secrets.compare_digest(api_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-API-Key header"
        )
    return api_key
