from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from .database import Base, SessionLocal, engine
from .models import EmissionFactor
from .routes import activity_logs, auth, dashboard, emissions, reports


app = FastAPI(title="EcoTrack", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(emissions.router)
app.include_router(reports.router)
app.include_router(activity_logs.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    _seed_emission_factors()


def _seed_emission_factors():
    seeds = [
        # Scope 2: electricity
        {"scope": 2, "activity_type": "grid_electricity_india", "factor_value": 0.82, "unit": "kWh", "source": "Example: India grid average"},
        {"scope": 2, "activity_type": "grid_electricity_global_avg", "factor_value": 0.45, "unit": "kWh", "source": "Example: global average"},
        # Scope 1: fuels
        {"scope": 1, "activity_type": "petrol", "factor_value": 2.31, "unit": "litre", "source": "Example: petrol combustion"},
        {"scope": 1, "activity_type": "diesel", "factor_value": 2.68, "unit": "litre", "source": "Example: diesel combustion"},
        {"scope": 1, "activity_type": "lpg", "factor_value": 1.51, "unit": "litre", "source": "Example: LPG combustion"},
        {"scope": 1, "activity_type": "natural_gas", "factor_value": 2.05, "unit": "kg", "source": "Example: natural gas (mass basis)"},
        # Scope 3: travel & logistics
        {"scope": 3, "activity_type": "domestic_flight", "factor_value": 0.255, "unit": "km", "source": "Example: domestic flight per km"},
        {"scope": 3, "activity_type": "rail_travel", "factor_value": 0.041, "unit": "km", "source": "Example: passenger rail per km"},
        {"scope": 3, "activity_type": "car_travel", "factor_value": 0.171, "unit": "km", "source": "Example: average car per km"},
        {"scope": 3, "activity_type": "freight_truck", "factor_value": 0.12, "unit": "km", "source": "Example: freight truck per km"},
        {"scope": 3, "activity_type": "paper", "factor_value": 1.3, "unit": "kg", "source": "Example: paper lifecycle per kg"},
    ]

    db = SessionLocal()
    try:
        existing = db.query(EmissionFactor).count()
        if existing > 0:
            return
        db.add_all([EmissionFactor(**row) for row in seeds])
        db.commit()
    finally:
        db.close()


@app.get("/health")
def health():
    """Load balancer / platform health check."""
    return {"status": "ok"}


# Serve the static frontend from the same origin (production / Docker). API routes are registered above.
_frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if _frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")
