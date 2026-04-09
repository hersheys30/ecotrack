from __future__ import annotations

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ActivityLog, EmissionsData, User
from ..schemas import DashboardSummary
from ..security import require_roles

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: Session = Depends(get_db),
    _user: Annotated[User, Depends(require_roles("Admin", "Analyst", "Viewer"))] = None,  # type: ignore[assignment]
):
    base = db.query(EmissionsData).join(ActivityLog, ActivityLog.id == EmissionsData.activity_log_id)
    if start is not None:
        base = base.filter(ActivityLog.date >= start)
    if end is not None:
        base = base.filter(ActivityLog.date <= end)

    total = base.with_entities(func.coalesce(func.sum(EmissionsData.calculated_co2e), 0.0)).scalar() or 0.0

    by_scope_rows = (
        base.with_entities(
            EmissionsData.scope.label("scope"),
            func.coalesce(func.sum(EmissionsData.calculated_co2e), 0.0).label("co2e"),
        )
        .group_by(EmissionsData.scope)
        .all()
    )
    by_scope = {f"Scope {r.scope}": float(r.co2e) for r in by_scope_rows}
    for s in (1, 2, 3):
        by_scope.setdefault(f"Scope {s}", 0.0)

    month_key = func.strftime("%Y-%m", ActivityLog.date)  # sqlite
    if db.bind and db.bind.dialect.name != "sqlite":
        month_key = func.to_char(ActivityLog.date, "YYYY-MM")  # postgres

    monthly_rows = (
        base.with_entities(
            month_key.label("month"),
            EmissionsData.scope.label("scope"),
            func.sum(EmissionsData.calculated_co2e).label("co2e"),
        )
        .group_by("month", EmissionsData.scope)
        .order_by("month")
        .all()
    )
    monthly_by_scope: dict[str, dict[str, float]] = {}
    for r in monthly_rows:
        monthly_by_scope.setdefault(r.month, {"Scope 1": 0.0, "Scope 2": 0.0, "Scope 3": 0.0})
        monthly_by_scope[r.month][f"Scope {r.scope}"] = float(r.co2e or 0.0)

    monthly_list = [{"month": m, **vals} for m, vals in monthly_by_scope.items()]

    by_activity_rows = (
        base.with_entities(
            ActivityLog.activity_type.label("activity_type"),
            func.sum(EmissionsData.calculated_co2e).label("co2e"),
        )
        .group_by(ActivityLog.activity_type)
        .order_by(func.sum(EmissionsData.calculated_co2e).desc())
        .limit(12)
        .all()
    )
    by_activity_type = [{"activity_type": r.activity_type, "co2e": float(r.co2e or 0.0)} for r in by_activity_rows]

    recent_rows = (
        db.query(
            ActivityLog.id,
            ActivityLog.scope,
            ActivityLog.activity_type,
            ActivityLog.quantity,
            ActivityLog.unit,
            ActivityLog.date,
            EmissionsData.calculated_co2e,
            ActivityLog.created_at,
        )
        .join(EmissionsData, EmissionsData.activity_log_id == ActivityLog.id)
        .order_by(ActivityLog.created_at.desc())
        .limit(10)
        .all()
    )
    recent_activity = [
        {
            "id": r.id,
            "scope": r.scope,
            "activity_type": r.activity_type,
            "quantity": float(r.quantity),
            "unit": r.unit,
            "date": r.date.isoformat(),
            "calculated_co2e": float(r.calculated_co2e),
            "created_at": r.created_at.isoformat(),
        }
        for r in recent_rows
    ]

    return DashboardSummary(
        total_co2e=float(total),
        by_scope=by_scope,
        monthly_by_scope=monthly_list,
        by_activity_type=by_activity_type,
        recent_activity=recent_activity,
    )

