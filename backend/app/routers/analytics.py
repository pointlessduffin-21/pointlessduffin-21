from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from typing import List, Optional
from datetime import datetime, timezone, date
import io
import csv

from app.database import get_db
from app.models import User, APIKey, SMSLog, UserRole
from app.schemas import CostBreakdown, UsageSummary, DashboardStats
from app.middleware.auth import get_current_user, require_role

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    today = date.today()
    month_start = today.replace(day=1)

    total_users = db.query(User).count()
    total_keys = db.query(APIKey).count()
    active_keys = db.query(APIKey).filter(APIKey.is_active == True).count()
    total_sms = db.query(SMSLog).count()

    today_logs = db.query(SMSLog).filter(
        func.date(SMSLog.created_at) == today.isoformat()
    )
    total_sms_today = today_logs.count()
    total_cost_today = db.query(func.coalesce(func.sum(SMSLog.cost), 0)).filter(
        func.date(SMSLog.created_at) == today.isoformat()
    ).scalar()

    total_cost_month = db.query(func.coalesce(func.sum(SMSLog.cost), 0)).filter(
        func.date(SMSLog.created_at) >= month_start.isoformat()
    ).scalar()

    return DashboardStats(
        total_users=total_users,
        total_api_keys=total_keys,
        active_api_keys=active_keys,
        total_sms_sent=total_sms,
        total_sms_today=total_sms_today,
        total_cost_today=round(float(total_cost_today), 4),
        total_cost_month=round(float(total_cost_month), 4),
    )


@router.get("/cost-breakdown", response_model=List[CostBreakdown])
def cost_breakdown(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    api_key_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = (
        db.query(
            APIKey.id.label("api_key_id"),
            APIKey.name.label("api_key_name"),
            User.username.label("username"),
            func.count(SMSLog.id).label("total_messages"),
            func.coalesce(func.sum(SMSLog.cost), 0).label("total_cost"),
            func.sum(
                case((SMSLog.status == "sent", 1), else_=0)
            ).label("sent_count"),
            func.sum(
                case((SMSLog.status == "failed", 1), else_=0)
            ).label("failed_count"),
        )
        .join(User, APIKey.user_id == User.id)
        .join(SMSLog, SMSLog.api_key_id == APIKey.id)
    )

    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        q = q.filter(APIKey.user_id == current_user.id)

    if start_date:
        q = q.filter(func.date(SMSLog.created_at) >= start_date)
    if end_date:
        q = q.filter(func.date(SMSLog.created_at) <= end_date)
    if api_key_id:
        q = q.filter(APIKey.id == api_key_id)

    rows = q.group_by(APIKey.id).order_by(func.sum(SMSLog.cost).desc()).all()

    return [
        CostBreakdown(
            api_key_id=r.api_key_id,
            api_key_name=r.api_key_name,
            username=r.username,
            total_messages=r.total_messages,
            total_cost=round(float(r.total_cost), 4),
            sent_count=r.sent_count,
            failed_count=r.failed_count,
        )
        for r in rows
    ]


@router.get("/usage-summary")
def usage_summary(
    period: str = Query(..., description="YYYY-MM"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    year, month = period.split("-")
    q = db.query(SMSLog).filter(
        extract("year", SMSLog.created_at) == int(year),
        extract("month", SMSLog.created_at) == int(month),
    )

    if current_user.role not in (UserRole.ADMIN, UserRole.MANAGER):
        user_key_ids = [k.id for k in db.query(APIKey).filter(APIKey.user_id == current_user.id).all()]
        q = q.filter(SMSLog.api_key_id.in_(user_key_ids) if user_key_ids else SMSLog.api_key_id == -1)

    total = q.count()
    total_cost = db.query(func.coalesce(func.sum(SMSLog.cost), 0)).filter(
        extract("year", SMSLog.created_at) == int(year),
        extract("month", SMSLog.created_at) == int(month),
    ).scalar()
    sent = q.filter(SMSLog.status == "sent").count()
    success_rate = (sent / total * 100) if total > 0 else 0

    return UsageSummary(
        period=period,
        total_messages=total,
        total_cost=round(float(total_cost), 4),
        success_rate=round(success_rate, 2),
    )


# ── CSV Exports ───────────────────────────────────────
@router.get("/export/csv")
def export_csv(
    export_type: str = Query(..., description="sms_logs | cost_breakdown"),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    api_key_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.MANAGER)),
):
    if export_type == "sms_logs":
        q = db.query(SMSLog).join(APIKey, SMSLog.api_key_id == APIKey.id, isouter=True).join(User, APIKey.user_id == User.id, isouter=True)
        if start_date:
            q = q.filter(func.date(SMSLog.created_at) >= start_date)
        if end_date:
            q = q.filter(func.date(SMSLog.created_at) <= end_date)
        if api_key_id:
            q = q.filter(SMSLog.api_key_id == api_key_id)

        rows = q.order_by(SMSLog.created_at.desc()).all()
        columns = ["id", "api_key_name", "username", "destination", "content", "port", "status", "credits_used", "cost", "ip_address", "created_at"]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        for row in rows:
            writer.writerow([
                row.id,
                row.api_key.name if row.api_key else "",
                row.api_key.owner.username if row.api_key and row.api_key.owner else "",
                row.destination,
                row.content,
                row.port,
                row.status,
                row.credits_used,
                row.cost,
                row.ip_address or "",
                row.created_at.isoformat() if row.created_at else "",
            ])

        filename = f"sms_logs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingResponse(
            iter([output.getvalue().encode("utf-8-sig")]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    elif export_type == "cost_breakdown":
        breakdown = cost_breakdown(start_date=start_date, end_date=end_date, api_key_id=api_key_id, db=db, current_user=current_user)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["api_key_id", "api_key_name", "username", "total_messages", "total_cost", "sent_count", "failed_count"])
        for r in breakdown:
            writer.writerow([r.api_key_id, r.api_key_name, r.username, r.total_messages, r.total_cost, r.sent_count, r.failed_count])

        filename = f"cost_breakdown_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
        return StreamingResponse(
            iter([output.getvalue().encode("utf-8-sig")]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    raise HTTPException(status_code=400, detail="Invalid export_type. Use 'sms_logs' or 'cost_breakdown'")
