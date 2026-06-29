from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    APP_NAME: str = "CubeSMS"
    DEBUG: bool = False
    DATABASE_URL: str = "sqlite:///./cubesms.db"
    SECRET_KEY: str = "cubesms-secret-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # T200 SMS Gateway
    SMS_GATEWAY_URL: str = "http://192.168.5.150/cgi/WebCGI"
    SMS_GATEWAY_ACCOUNT: str = "apiuser"
    SMS_GATEWAY_PASSWORD: str = "apipass"
    SMS_DEFAULT_PORT: int = 1

    # Rate limits
    RATE_LIMIT_GLOBAL: str = "100/minute"
    RATE_LIMIT_PER_KEY: str = "30/minute"

    # Redis (optional, falls back to in-memory)
    REDIS_URL: Optional[str] = None

    # Cost per SMS (in cents, for billing)
    SMS_COST_PER_MESSAGE: float = 0.05

    class Config:
        env_file = ".env"


settings = Settings()
