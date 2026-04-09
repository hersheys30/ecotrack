from __future__ import annotations

from datetime import date
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from ..calculations.ghg_engine import UnitConversionError, calculate_co2e
from ..database import get_db
from ..models import ActivityLog, EmissionFactor, EmissionsData, User
from ..schemas import EmissionFactorOut, LogEmissionResponse, ActivityLogCreate
from ..security import get_current_user, require_roles

router = APIRouter(tags=["emissions"])


@router.get("/emission-factors", response_model=list[EmissionFactorOut])
def list_emission_factors(
    scope: Optional[int] = Query(default=None, ge=1, le=3),
    db: Session = Depends(get_db),
    _user: User = Depends(require_roles("Admin", "Analyst", "Viewer")),
):
    q = db.query(EmissionFactor)
    if scope is not None:
        q = q.filter(EmissionFactor.scope == scope)
    return q.order_by(EmissionFactor.scope.asc(), EmissionFactor.activity_type.asc()).all()


@router.post("/emissions/log", response_model=LogEmissionResponse)
def log_emission(
    payload: ActivityLogCreate,
    db: Session = Depends(get_db),
    user: Annotated[User, Depends(require_roles("Admin", "Analyst"))] = None,  # type: ignore[assignment]
):
    factor = (
        db.query(EmissionFactor)
        .filter(and_(EmissionFactor.scope == payload.scope, EmissionFactor.activity_type == payload.activity_type))
        .order_by(EmissionFactor.updated_at.desc())
        .first()
    )
    if not factor:
        raise HTTPException(status_code=404, detail="No emission factor found for scope/activity_type")

    try:
        co2e = calculate_co2e(payload.quantity, payload.unit, factor.factor_value, factor.unit)
    except UnitConversionError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    log = ActivityLog(
        user_id=user.id,
        scope=payload.scope,
        activity_type=payload.activity_type,
        quantity=payload.quantity,
        unit=payload.unit,
        date=payload.date,
        notes=payload.notes,
    )
    db.add(log)
    db.flush()  # get log.id

    emissions = EmissionsData(
        activity_log_id=log.id,
        emission_factor_id=factor.id,
        calculated_co2e=co2e,
        scope=payload.scope,
    )
    db.add(emissions)
    db.commit()
    db.refresh(log)
    db.refresh(emissions)
    db.refresh(factor)

    return LogEmissionResponse(activity_log=log, emissions=emissions, factor=factor)


@router.get("/emissions")
def list_emissions(
    scope: Optional[int] = Query(default=None, ge=1, le=3),
    start: Optional[date] = None,
    end: Optional[date] = None,
    db: Session = Depends(get_db),
    _user: Annotated[User, Depends(require_roles("Admin", "Analyst", "Viewer"))] = None,  # type: ignore[assignment]
):
    q = (
        db.query(
            EmissionsData.id.label("id"),
            EmissionsData.scope.label("scope"),
            EmissionsData.calculated_co2e.label("calculated_co2e"),
            ActivityLog.activity_type.label("activity_type"),
            ActivityLog.date.label("date"),
        )
        .join(ActivityLog, ActivityLog.id == EmissionsData.activity_log_id)
    )
    if scope is not None:
        q = q.filter(EmissionsData.scope == scope)
    if start is not None:
        q = q.filter(ActivityLog.date >= start)
    if end is not None:
        q = q.filter(ActivityLog.date <= end)

    rows = q.order_by(ActivityLog.date.desc()).all()
    return [
        {
            "id": r.id,
            "scope": r.scope,
            "calculated_co2e": float(r.calculated_co2e),
            "activity_type": r.activity_type,
            "date": r.date.isoformat(),
        }
        for r in rows
    ]
