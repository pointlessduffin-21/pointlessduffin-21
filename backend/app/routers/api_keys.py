from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from app.database import get_db
from app.models import User, APIKey, UserRole
from app.schemas import APIKeyCreate, APIKeyUpdate, APIKeyOut, APIKeyCreated
from app.utils.keys import generate_api_key
from app.middleware.auth import get_current_user, require_role

router = APIRouter(prefix="/api/keys", tags=["api_keys"])


@router.get("/", response_model=List[APIKeyOut])
def list_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role in (UserRole.ADMIN, UserRole.MANAGER):
        return db.query(APIKey).order_by(APIKey.created_at.desc()).all()
    return (
        db.query(APIKey)
        .filter(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
        .all()
    )


@router.post("/", response_model=APIKeyCreated, status_code=201)
def create_key(
    body: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    full_key, prefix, key_hash = generate_api_key()

    api_key = APIKey(
        name=body.name,
        key_prefix=prefix,
        key_hash=key_hash,
        user_id=current_user.id,
        expires_at=body.expires_at,
        rate_limit_per_minute=body.rate_limit_per_minute,
        allowed_ips=body.allowed_ips,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        full_key=full_key,
        prefix=prefix,
        expires_at=api_key.expires_at,
    )


@router.get("/{key_id}", response_model=APIKeyOut)
def get_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(APIKey).filter(APIKey.id == key_id)
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        q = q.filter(APIKey.user_id == current_user.id)
    key = q.first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    return key


@router.put("/{key_id}", response_model=APIKeyOut)
def update_key(
    key_id: int,
    body: APIKeyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(APIKey).filter(APIKey.id == key_id)
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        q = q.filter(APIKey.user_id == current_user.id)
    key = q.first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    if body.name is not None:
        key.name = body.name
    if body.is_active is not None:
        key.is_active = body.is_active
    if body.expires_at is not None:
        key.expires_at = body.expires_at
    if body.rate_limit_per_minute is not None:
        key.rate_limit_per_minute = body.rate_limit_per_minute
    if body.allowed_ips is not None:
        key.allowed_ips = body.allowed_ips
    db.commit()
    db.refresh(key)
    return key


@router.delete("/{key_id}", status_code=204)
def delete_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(APIKey).filter(APIKey.id == key_id)
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        q = q.filter(APIKey.user_id == current_user.id)
    key = q.first()
    if not key:
        raise HTTPException(status_code=404, detail="API key not found")
    db.delete(key)
    db.commit()
