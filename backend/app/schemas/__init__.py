from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from app.models import UserRole


# ── Auth ──────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    username: str
    password: str


# ── Users ─────────────────────────────────────────────
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    role: UserRole = UserRole.USER


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=6)


class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ── API Keys ──────────────────────────────────────────
class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    expires_at: Optional[datetime] = None
    rate_limit_per_minute: int = Field(default=30, ge=1, le=300)
    allowed_ips: Optional[str] = None


class APIKeyUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    expires_at: Optional[datetime] = None
    rate_limit_per_minute: Optional[int] = Field(None, ge=1, le=300)
    allowed_ips: Optional[str] = None


class APIKeyOut(BaseModel):
    id: int
    name: str
    key_prefix: str
    is_active: bool
    expires_at: Optional[datetime]
    rate_limit_per_minute: int
    allowed_ips: Optional[str]
    created_at: datetime
    last_used_at: Optional[datetime]
    user_id: int

    class Config:
        from_attributes = True


class APIKeyCreated(BaseModel):
    """Returned only once when key is created — includes the full key."""
    id: int
    name: str
    full_key: str
    prefix: str
    expires_at: Optional[datetime]
    message: str = "Store this key securely — it will never be shown again."


# ── SMS ───────────────────────────────────────────────
class SMSRequest(BaseModel):
    destination: str = Field(..., min_length=8, max_length=20, pattern=r"^\d+$")
    content: str = Field(..., min_length=1, max_length=500)
    port: int = Field(default=1, ge=1, le=32)


class SMSResponse(BaseModel):
    id: int
    destination: str
    content: str
    status: str
    gateway_response: Optional[str]
    credits_used: int
    cost: float
    created_at: datetime


class SMSLogOut(BaseModel):
    id: int
    api_key_id: int
    api_key_name: Optional[str] = None
    username: Optional[str] = None
    destination: str
    content: str
    port: int
    status: str
    gateway_response: Optional[str]
    credits_used: int
    cost: float
    ip_address: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Analytics / Reports ───────────────────────────────
class CostBreakdown(BaseModel):
    api_key_id: int
    api_key_name: str
    username: str
    total_messages: int
    total_cost: float
    sent_count: int
    failed_count: int


class UsageSummary(BaseModel):
    period: str  # e.g. "2026-06"
    total_messages: int
    total_cost: float
    success_rate: float


class DashboardStats(BaseModel):
    total_users: int
    total_api_keys: int
    active_api_keys: int
    total_sms_sent: int
    total_sms_today: int
    total_cost_today: float
    total_cost_month: float
