from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field


Role = Literal["Admin", "Analyst", "Viewer"]


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role = "Viewer"
    organisation: Optional[str] = Field(default=None, max_length=200)


class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    organisation: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class EmissionFactorOut(BaseModel):
    id: int
    scope: int
    activity_type: str
    factor_value: float
    unit: str
    source: Optional[str] = None
    updated_at: datetime

    class Config:
        from_attributes = True


class ActivityLogCreate(BaseModel):
    scope: int = Field(ge=1, le=3)
    activity_type: str = Field(min_length=1, max_length=120)
    quantity: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=32)
    date: date
    notes: Optional[str] = None


class ActivityLogOut(BaseModel):
    id: int
    user_id: int
    scope: int
    activity_type: str
    quantity: float
    unit: str
    date: date
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class EmissionsDataOut(BaseModel):
    id: int
    activity_log_id: int
    emission_factor_id: int
    calculated_co2e: float
    scope: int
    created_at: datetime

    class Config:
        from_attributes = True


class LogEmissionResponse(BaseModel):
    activity_log: ActivityLogOut
    emissions: EmissionsDataOut
    factor: EmissionFactorOut


class DashboardSummary(BaseModel):
    total_co2e: float
    by_scope: dict[str, float]
    monthly_by_scope: list[dict]
    by_activity_type: list[dict]
    recent_activity: list[dict]
