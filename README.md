# EcoTrack

Multi-scope (Scope 1/2/3) carbon emissions analytics web app: **FastAPI** backend, **SQLAlchemy** database, **HTML/CSS/JS** frontend.

- **Repository:** [github.com/hersheys30/ecotrack](https://github.com/hersheys30/ecotrack)

## Run locally

```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 8000
```

Open **http://127.0.0.1:8000/** (UI + API on the same origin). API docs: **http://127.0.0.1:8000/docs**

Configure DB with `DATABASE_URL` (PostgreSQL recommended). Default is local SQLite `./ecotrack.db`. Set `JWT_SECRET_KEY` for production.

## Deploy

See **[DEPLOY.md](DEPLOY.md)** for Docker deployment (Render, Fly.io, VPS).

## API (summary)

- `POST /auth/register`, `POST /auth/login`
- `GET /dashboard/summary`
- `GET /emissions`, `POST /emissions/log`
- `GET /emission-factors`
- `GET /reports/export?format=csv`
- `GET /activity-logs`
