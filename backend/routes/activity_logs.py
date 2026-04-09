from __future__ import annotations

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ActivityLog, EmissionsData, User
from ..security import require_roles

router = APIRouter(tags=["activity-logs"])


@router.get("/activity-logs")
def list_activity_logs(
    scope: Optional[int] = Query(default=None, ge=1, le=3),
    start: Optional[date] = None,
    end: Optional[date] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _user: Annotated[User, Depends(require_roles("Admin", "Analyst", "Viewer"))] = None,  # type: ignore[assignment]
):
    q = (
        db.query(
            ActivityLog.id,
            ActivityLog.user_id,
            ActivityLog.scope,
            ActivityLog.activity_type,
            ActivityLog.quantity,
            ActivityLog.unit,
            ActivityLog.date,
            ActivityLog.notes,
            ActivityLog.created_at,
            EmissionsData.calculated_co2e,
        )
        .outerjoin(EmissionsData, EmissionsData.activity_log_id == ActivityLog.id)
    )
    if scope is not None:
        q = q.filter(ActivityLog.scope == scope)
    if start is not None:
        q = q.filter(ActivityLog.date >= start)
    if end is not None:
        q = q.filter(ActivityLog.date <= end)
    rows = q.order_by(ActivityLog.created_at.desc()).offset(offset).limit(limit).all()

    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "scope": r.scope,
            "activity_type": r.activity_type,
            "quantity": float(r.quantity),
            "unit": r.unit,
            "date": r.date.isoformat(),
            "notes": r.notes,
            "created_at": r.created_at.isoformat(),
            "calculated_co2e": float(r.calculated_co2e) if r.calculated_co2e is not None else None,
        }
        for r in rows
    ]

