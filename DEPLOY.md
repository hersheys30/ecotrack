# Deploy EcoTrack

EcoTrack runs as **one service**: FastAPI serves the API and the static `frontend/` (same origin), so the browser can call `/auth/login`, `/dashboard/summary`, etc. without CORS issues.

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PORT` | Auto | Set by the host (e.g. Render, Fly). Defaults to `8000` in Docker. |
| `DATABASE_URL` | Recommended | PostgreSQL URL. If unset, the app uses SQLite (`./ecotrack.db`). **SQLite on PaaS is ephemeral** (data can be lost on restart). |
| `JWT_SECRET_KEY` | **Yes (production)** | Long random string. If unchanged, tokens can be forged. |
| `CORS_ALLOW_ORIGINS` | Optional | Comma-separated origins; default `*` is fine when UI and API share one URL. |

**PostgreSQL:** Render/Heroku often provide `postgres://...`. The app normalizes this to `postgresql+psycopg2://...` automatically.

## Option A: [Render](https://render.com) (Docker)

1. Push this repo to GitHub (e.g. [hersheys30/ecotrack](https://github.com/hersheys30/ecotrack)).
2. **New → Web Service** → connect the repo.
3. **Runtime:** Docker (uses root `Dockerfile`).
4. **Instance type:** Free (cold starts are normal on free tier).
5. **Environment:**
   - `JWT_SECRET_KEY` → generate a long random string (e.g. `openssl rand -hex 32`).
   - **Optional:** Create **PostgreSQL** on Render, then copy **Internal Database URL** into `DATABASE_URL`.
6. Deploy. Open the service URL — you should see the **login page**. API docs: `https://YOUR-SERVICE.onrender.com/docs`.

## Option B: [Fly.io](https://fly.io)

1. Install the Fly CLI and run `fly launch` in this directory (uses `Dockerfile`).
2. Set secrets: `fly secrets set JWT_SECRET_KEY=...` and optionally `DATABASE_URL=...`.
3. `fly deploy`.

## Option C: Any VPS (Docker)

```bash
docker build -t ecotrack .
docker run -e PORT=8000 -e JWT_SECRET_KEY=your-secret -p 8000:8000 ecotrack
```

Open `http://SERVER_IP:8000`.

## Local production-style run

From the project root (not `file://` — use the server so `config.js` uses `window.location.origin`):

```bash
pip install -r backend/requirements.txt
set JWT_SECRET_KEY=dev-secret
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000/`.
