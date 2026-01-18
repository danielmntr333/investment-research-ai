"""API key authentication."""
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """
    Verify API key and check rate limits.
    
    Returns:
        User object if valid
    
    Raises:
        HTTPException if invalid or quota exceeded
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required")
    
    # To be implemented: Check against database
    # To be implemented: Check rate limits
    
    return {"user_id": "test", "email": "test@example.com"}
