from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models import APIKey, SMSLog, User, UserRole, AppSettings
from app.schemas import SMSRequest, SMSResponse, SMSLogOut
from app.services.sms_gateway import send_sms
from app.middleware.auth import get_current_user, require_role, get_api_key_from_request
from app.config import settings

router = APIRouter(prefix="/api/sms", tags=["sms"])


# ── Internal (web UI) SMS sending ─────────────────────
@router.post("/send", response_model=SMSResponse)
def send_sms_internal(
    body: SMSRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _do_send_sms(body, db, api_key=None, request=None, user=current_user)


# ── External API (API key) SMS sending ────────────────
ext_router = APIRouter(prefix="/api/v1", tags=["external"])


@ext_router.post("/sms/send", response_model=SMSResponse)
async def send_sms_external(
    body: SMSRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    # Validate API key
    api_key = await get_api_key_from_request(request, db)
    if api_key is None:
        return  # handled by dependency

    # Check IP whitelist
    if api_key.allowed_ips:
        client_ip = request.client.host if request.client else "unknown"
        allowed = [ip.strip() for ip in api_key.allowed_ips.split(",")]
        if client_ip not in allowed and "0.0.0.0" not in allowed:
            raise HTTPException(status_code=403, detail=f"IP {client_ip} not allowed")

    return await _do_send_sms_async(body, db, api_key=api_key, request=request)


async def _do_send_sms_async(body: SMSRequest, db: Session, api_key: APIKey, request: Request | None = None) -> SMSResponse:
    """Async version for external API calls."""
    # Load DB settings (fall back to config defaults)
    app_set = db.query(AppSettings).first()
    gw_url = app_set.gateway_url if app_set else None
    gw_acct = app_set.gateway_account if app_set else None
    gw_pass = app_set.gateway_password if app_set else None
    cost_per = app_set.sms_cost_per_message if app_set else settings.SMS_COST_PER_MESSAGE

    # Send via gateway
    result = await send_sms(body.destination, body.content, body.port,
                            gateway_url=gw_url, gateway_account=gw_acct, gateway_password=gw_pass)
    status_str = "sent" if result["success"] else "failed"
    cost = result["credits_used"] * cost_per

    log = SMSLog(
        api_key_id=api_key.id,
        destination=body.destination,
        content=body.content,
        port=body.port,
        status=status_str,
        gateway_response=result["raw_response"],
        credits_used=result["credits_used"],
        cost=cost,
        ip_address=request.client.host if request and request.client else None,
        user_agent=request.headers.get("User-Agent", "")[:500] if request else None,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return SMSResponse(
        id=log.id,
        destination=log.destination,
        content=log.content,
        status=log.status,
        gateway_response=log.gateway_response,
        credits_used=log.credits_used,
        cost=log.cost,
        created_at=log.created_at,
    )


def _do_send_sms(body: SMSRequest, db: Session, api_key: APIKey | None, request: Request | None, user: User | None) -> SMSResponse:
    """Sync wrapper for internal calls that need async SMS gateway."""
    # Load DB settings
    app_set = db.query(AppSettings).first()
    gw_url = app_set.gateway_url if app_set else None
    gw_acct = app_set.gateway_account if app_set else None
    gw_pass = app_set.gateway_password if app_set else None
    cost_per = app_set.sms_cost_per_message if app_set else settings.SMS_COST_PER_MESSAGE

    import asyncio
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(send_sms(body.destination, body.content, body.port,
                                                   gateway_url=gw_url, gateway_account=gw_acct, gateway_password=gw_pass))
    finally:
        loop.close()

    status_str = "sent" if result["success"] else "failed"
    cost = result["credits_used"] * cost_per

    log = SMSLog(
        api_key_id=api_key.id if api_key else 0,
        destination=body.destination,
        content=body.content,
        port=body.port,
        status=status_str,
        gateway_response=result["raw_response"],
        credits_used=result["credits_used"],
        cost=cost,
        ip_address=request.client.host if request and request.client else None,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return SMSResponse(
        id=log.id,
        destination=log.destination,
        content=log.content,
        status=log.status,
        gateway_response=log.gateway_response,
        credits_used=log.credits_used,
        cost=log.cost,
        created_at=log.created_at,
    )


# ── SMS Logs / History ────────────────────────────────
@router.get("/logs", response_model=List[SMSLogOut])
def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    status_filter: Optional[str] = Query(None, alias="status"),
    key_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(SMSLog).join(APIKey, SMSLog.api_key_id == APIKey.id, isouter=True).join(User, APIKey.user_id == User.id, isouter=True)

    # Non-admin users only see their own logs
    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        user_key_ids = [k.id for k in db.query(APIKey).filter(APIKey.user_id == current_user.id).all()]
        q = q.filter(SMSLog.api_key_id.in_(user_key_ids) if user_key_ids else SMSLog.api_key_id == -1)

    if status_filter:
        q = q.filter(SMSLog.status == status_filter)
    if key_id:
        q = q.filter(SMSLog.api_key_id == key_id)
    if start_date:
        q = q.filter(SMSLog.created_at >= datetime.fromisoformat(start_date))
    if end_date:
        q = q.filter(SMSLog.created_at <= datetime.fromisoformat(end_date))

    total = q.count()
    logs = q.order_by(SMSLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for log in logs:
        result.append(SMSLogOut(
            id=log.id,
            api_key_id=log.api_key_id,
            api_key_name=log.api_key.name if log.api_key else None,
            username=log.api_key.owner.username if log.api_key and log.api_key.owner else None,
            destination=log.destination,
            content=log.content,
            port=log.port,
            status=log.status,
            gateway_response=log.gateway_response,
            credits_used=log.credits_used,
            cost=log.cost,
            ip_address=log.ip_address,
            created_at=log.created_at,
        ))
    return result
