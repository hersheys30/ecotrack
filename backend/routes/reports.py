from __future__ import annotations

import csv
import io
from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ActivityLog, EmissionsData, User
from ..security import require_roles

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/export")
def export_report_csv(
    format: str = Query(default="csv", pattern="^(csv)$"),
    scope: Optional[int] = Query(default=None, ge=1, le=3),
    start: Optional[date] = None,
    end: Optional[date] = None,
    activity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _user: Annotated[User, Depends(require_roles("Admin", "Analyst"))] = None,  # type: ignore[assignment]
):
    q = (
        db.query(
            ActivityLog.id.label("activity_log_id"),
            ActivityLog.user_id.label("user_id"),
            ActivityLog.scope.label("scope"),
            ActivityLog.activity_type.label("activity_type"),
            ActivityLog.quantity.label("quantity"),
            ActivityLog.unit.label("unit"),
            ActivityLog.date.label("date"),
            ActivityLog.notes.label("notes"),
            EmissionsData.calculated_co2e.label("calculated_co2e"),
            ActivityLog.created_at.label("created_at"),
        )
        .join(EmissionsData, EmissionsData.activity_log_id == ActivityLog.id)
    )
    if scope is not None:
        q = q.filter(ActivityLog.scope == scope)
    if start is not None:
        q = q.filter(ActivityLog.date >= start)
    if end is not None:
        q = q.filter(ActivityLog.date <= end)
    if activity_type:
        q = q.filter(ActivityLog.activity_type == activity_type)

    rows = q.order_by(ActivityLog.date.desc()).all()

    def iter_csv():
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(
            [
                "activity_log_id",
                "user_id",
                "scope",
                "activity_type",
                "quantity",
                "unit",
                "date",
                "calculated_co2e_kg",
                "notes",
                "created_at",
            ]
        )
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)

        for r in rows:
            writer.writerow(
                [
                    r.activity_log_id,
                    r.user_id,
                    r.scope,
                    r.activity_type,
                    r.quantity,
                    r.unit,
                    r.date.isoformat(),
                    float(r.calculated_co2e),
                    r.notes or "",
                    r.created_at.isoformat(),
                ]
            )
            yield buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)

    return StreamingResponse(
        iter_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="ecotrack_report.csv"'},
    )
