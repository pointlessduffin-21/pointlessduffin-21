from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    USER = "user"
    VIEWER = "viewer"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    api_keys = relationship("APIKey", back_populates="owner", cascade="all, delete-orphan")


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    key_prefix = Column(String(12), unique=True, index=True, nullable=False)  # First 8 chars visible
    key_hash = Column(String(255), nullable=False)  # Full key bcrypt hash
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    rate_limit_per_minute = Column(Integer, default=30)
    allowed_ips = Column(String(500), nullable=True)  # Comma-separated IPs
    created_at = Column(DateTime, server_default=func.now())
    last_used_at = Column(DateTime, nullable=True)

    owner = relationship("User", back_populates="api_keys")
    sms_logs = relationship("SMSLog", back_populates="api_key", cascade="all, delete-orphan")


class SMSLog(Base):
    __tablename__ = "sms_logs"

    id = Column(Integer, primary_key=True, index=True)
    api_key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=False)
    destination = Column(String(20), nullable=False)
    content = Column(String(500), nullable=False)
    port = Column(Integer, default=1)
    status = Column(String(20), default="pending")  # pending, sent, failed, delivered
    gateway_response = Column(String(1000), nullable=True)
    credits_used = Column(Integer, default=1)
    cost = Column(Float, default=0.0)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    api_key = relationship("APIKey", back_populates="sms_logs")


class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    gateway_url = Column(String(500), default="http://192.168.5.150/cgi/WebCGI")
    gateway_account = Column(String(255), default="apiuser")
    gateway_password = Column(String(255), default="apipass")
    default_port = Column(Integer, default=1)
    sms_cost_per_message = Column(Float, default=0.05)
    test_destination = Column(String(20), default="09993511225")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
