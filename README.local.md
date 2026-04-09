# EcoTrack

Multi-scope (Scope 1/2/3) carbon emissions analytics web app.

## Backend (FastAPI)

### Setup

Create a virtualenv, then:

```bash
pip install -r backend/requirements.txt
```

### Configure (PostgreSQL recommended)

Set `DATABASE_URL`:

- Postgres example: `postgresql+psycopg2://user:password@localhost:5432/ecotrack`
- Default (if unset): local SQLite `./ecotrack.db`

Also set:

- `JWT_SECRET_KEY`: change in production

### Run

```bash
uvicorn backend.main:app --reload
```

On first run the app will create tables and seed `emission_factors`.

## API

- `POST /auth/register`
- `POST /auth/login`
- `GET /dashboard/summary`
- `GET /emissions?scope=&start=&end=`
- `POST /emissions/log`
- `GET /emission-factors`
- `GET /reports/export?format=csv`
- `GET /activity-logs`

