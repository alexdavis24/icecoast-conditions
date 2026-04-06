# icecoast-conditions

Local-first web app for tracking Northeast ski conditions and what is happening across the region.

## Current shape

- `src/frontend/` contains a minimal React sample app
- `src/backend/` contains a minimal FastAPI API
- `src/pipeline/` is reserved for future Python workers that will shape data for Postgres
- `docker-compose.yml` brings up the frontend and backend together for local development

## Run it locally

Copy `.env.example` to `.env` first, then start the stack.

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`

## Pipeline

Run the Open-Meteo backfill from the repo root with:

```bash
./icecoast-pipeline backfill --location stowe-vt --start 2024-01-01 --end 2024-01-31
```

The wrapper expects `DATABASE_URL` to point at the running Postgres instance.
