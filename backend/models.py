from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base, utcnow


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="Viewer")
    organisation: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    activity_logs: Mapped[list["ActivityLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class EmissionFactor(Base):
    __tablename__ = "emission_factors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scope: Mapped[int] = mapped_column(Integer, nullable=False)  # 1,2,3
    activity_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    factor_value: Mapped[float] = mapped_column(Float, nullable=False)  # kgCO2e per unit
    unit: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. kWh, litre, km, kg
    source: Mapped[str | None] = mapped_column(String(255), nullable=True)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (UniqueConstraint("scope", "activity_type", name="uq_factor_scope_activity"),)

    emissions_rows: Mapped[list["EmissionsData"]] = relationship(back_populates="emission_factor")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    scope: Mapped[int] = mapped_column(Integer, nullable=False)  # duplicated for easy filtering
    activity_type: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(32), nullable=False)
    date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user: Mapped["User"] = relationship(back_populates="activity_logs")
    emissions_data: Mapped["EmissionsData"] = relationship(
        back_populates="activity_log", uselist=False, cascade="all, delete-orphan"
    )


class EmissionsData(Base):
    __tablename__ = "emissions_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    activity_log_id: Mapped[int] = mapped_column(
        ForeignKey("activity_logs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    emission_factor_id: Mapped[int] = mapped_column(
        ForeignKey("emission_factors.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    calculated_co2e: Mapped[float] = mapped_column(Float, nullable=False)  # kgCO2e
    scope: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    activity_log: Mapped["ActivityLog"] = relationship(back_populates="emissions_data")
    emission_factor: Mapped["EmissionFactor"] = relationship(back_populates="emissions_rows")
