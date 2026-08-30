from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, Optional
import logging

from app.core.config import settings
from app.db.supabase_client import get_supabase_client

logger = logging.getLogger("docmind")
security = HTTPBearer(auto_error=False)

def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)) -> Dict[str, Any]:
    token: Optional[str] = None
    if credentials and credentials.credentials:
        token = credentials.credentials

    if token:
        client = get_supabase_client()
        if client:
            try:
                user_res = client.auth.get_user(token)
                if user_res and user_res.user:
                    user = user_res.user
                    return {
                        "id": str(user.id),
                        "email": getattr(user, "email", ""),
                        "user_metadata": getattr(user, "user_metadata", {}) or {},
                    }
            except Exception as e:
                logger.warning(f"Failed to verify Supabase token: {e}")

    # Development / Test fallback mode (ONLY when explicitly enabled in settings)
    if settings.AUTH_ALLOW_DEV_FALLBACK:
        logger.info("AUTH_ALLOW_DEV_FALLBACK is enabled. Returning fallback demo user identity.")
        return {
            "id": "00000000-0000-0000-0000-000000000001",
            "email": "demo@docmind.ai",
            "user_metadata": {"full_name": "Demo Student User"},
        }

    # Strict production requirement: Rejects missing/invalid token with 401 Unauthorized
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials. Bearer token is missing or invalid.",
        headers={"WWW-Authenticate": "Bearer"},
    )
