# icecoast-conditions

Local-first web app for tracking Northeast ski conditions and what is happening across the region.

## Current shape

- `src/frontend/` contains a minimal React sample app
- `src/backend/` contains a minimal FastAPI API
- `src/pipeline/` is reserved for future Python workers that will shape data for Postgres
- `docker-compose.yml` brings up the frontend and backend together for local development

## Run it locally

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
