from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.models import User, UserRole
from app.utils.auth import hash_password
from app.config import settings as app_settings
from app.routers import auth, users, api_keys, sms, analytics, settings as settings_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed default admin
    Base.metadata.create_all(bind=engine)
    seed_default_admin()
    yield


def seed_default_admin():
    """Create default admin user if none exists."""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.role == UserRole.ADMIN).first():
            admin = User(
                username="admin",
                email="admin@cubesms.local",
                hashed_password=hash_password("admin123"),
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            print("[CubeSMS] Default admin created: admin / admin123")
    finally:
        db.close()


app = FastAPI(
    title=app_settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(api_keys.router)
app.include_router(sms.router)
app.include_router(analytics.router)

# Settings
app.include_router(settings_router.router)

# External API v1 (API key auth)
app.include_router(sms.ext_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": app_settings.APP_NAME, "version": "1.0.0"}
