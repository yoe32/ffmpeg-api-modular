from fastapi import Depends, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from app.core.config import settings
api_key_header = APIKeyHeader(name="X-Api-Key", auto_error=False)
async def require_api_key(key: str = Depends(api_key_header)):
    if not settings.API_KEY:
        return True
    if key == settings.API_KEY:
        return True
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
