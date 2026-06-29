from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.models import AppSettings, User, UserRole
from app.middleware.auth import get_current_user, require_role
from app.services.sms_gateway import send_sms

router = APIRouter(prefix="/api/settings", tags=["settings"])


class SettingsUpdate(BaseModel):
    gateway_url: Optional[str] = None
    gateway_account: Optional[str] = None
    gateway_password: Optional[str] = None
    default_port: Optional[int] = Field(None, ge=1, le=32)
    sms_cost_per_message: Optional[float] = Field(None, ge=0)
    test_destination: Optional[str] = Field(None, min_length=8, max_length=20)


class SettingsOut(BaseModel):
    id: int
    gateway_url: str
    gateway_account: str
    gateway_password: str
    default_port: int
    sms_cost_per_message: float
    test_destination: str
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestResult(BaseModel):
    success: bool
    destination: str
    gateway_response: str
    credits_used: int
    cost: float


def _get_settings(db: Session) -> AppSettings:
    s = db.query(AppSettings).first()
    if not s:
        s = AppSettings()
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


@router.get("/", response_model=SettingsOut)
def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER)),
):
    return _get_settings(db)


@router.put("/", response_model=SettingsOut)
def update_settings(
    body: SettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN)),
):
    s = _get_settings(db)
    if body.gateway_url is not None:
        s.gateway_url = body.gateway_url
    if body.gateway_account is not None:
        s.gateway_account = body.gateway_account
    if body.gateway_password is not None:
        s.gateway_password = body.gateway_password
    if body.default_port is not None:
        s.default_port = body.default_port
    if body.sms_cost_per_message is not None:
        s.sms_cost_per_message = body.sms_cost_per_message
    if body.test_destination is not None:
        s.test_destination = body.test_destination
    db.commit()
    db.refresh(s)
    return s


@router.post("/test", response_model=TestResult)
async def test_connection(
    body: Optional[SettingsUpdate] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER)),
):
    """Send a test SMS using current or provided settings."""
    s = _get_settings(db)

    # Override with provided values if any
    url = body.gateway_url if body and body.gateway_url else s.gateway_url
    account = body.gateway_account if body and body.gateway_account else s.gateway_account
    password = body.gateway_password if body and body.gateway_password else s.gateway_password
    port = body.default_port if body and body.default_port else s.default_port
    destination = body.test_destination if body and body.test_destination else s.test_destination
    cost_per = body.sms_cost_per_message if body and body.sms_cost_per_message else s.sms_cost_per_message

    # Send test via gateway
    result = await send_sms(destination, "CubeSMS test message", port)

    return TestResult(
        success=result["success"],
        destination=destination,
        gateway_response=result["raw_response"],
        credits_used=result["credits_used"],
        cost=round(result["credits_used"] * cost_per, 4),
    )
