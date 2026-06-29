from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, APIKey, UserRole
from app.utils.auth import decode_token, verify_password
import re

security = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Extracts the logged-in user from the JWT Bearer token."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


def require_role(*roles: UserRole):
    """Dependency factory: only allow users with one of the given roles."""

    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return checker


async def get_api_key_from_header(
    authorization: str | None = None,
    db: Session = Depends(get_db),
) -> APIKey:
    """
    Validates an API key from the X-API-Key header (or Bearer token for API access).
    Used for external API endpoints.
    """
    from fastapi import Request

    # This is used as a dependency — we get the request via a trick
    raise NotImplementedError("Use get_api_key_dependency instead")


async def get_api_key_from_request(
    request: "Request",
    db: Session = Depends(get_db),
) -> APIKey:
    """Validates API key from X-API-Key header."""
    api_key_raw = request.headers.get("X-API-Key")
    if not api_key_raw:
        # Also try Bearer token
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            api_key_raw = auth[7:]

    if not api_key_raw:
        raise HTTPException(status_code=401, detail="API key required (X-API-Key header)")

    # Find by prefix first, then verify
    prefix = api_key_raw[:8]
    keys = db.query(APIKey).filter(
        APIKey.key_prefix == prefix,
        APIKey.is_active == True,
    ).all()

    for key in keys:
        if verify_password(api_key_raw, key.key_hash):
            # Check expiration
            from datetime import datetime, timezone
            if key.expires_at and key.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(status_code=403, detail="API key has expired")

            # Update last_used
            key.last_used_at = datetime.now(timezone.utc)
            db.commit()
            return key

    raise HTTPException(status_code=403, detail="Invalid API key")
