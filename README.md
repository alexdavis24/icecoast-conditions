# icecoast-conditions

Local-first web app for tracking Northeast ski conditions and what is happening across the region.

## Hosting

Releases are built as container images and published to GitHub Container
Registry. A GitHub Actions workflow deploys tagged releases over SSH to an
Ubuntu host that runs dev and production stacks side by side behind Caddy.

- `vX.Y.Z-dev` deploys `dev.icecoastnicecoast.com`
- `vX.Y.Z` deploys `icecoastnicecoast.com`

Deployment assets live in [`deploy/`](deploy/), and the workflow is defined in
[`/.github/workflows/deploy.yml`](.github/workflows/deploy.yml).

Required GitHub Actions secrets:

- `GHCR_USERNAME`
- `GHCR_TOKEN`
- `TAILSCALE_AUTHKEY`
- `TAILSCALE_IP`
- `SSH_USER`
- `SSH_PRIVATE_KEY`
- `POSTGRES_PASSWORD`

## Current shape

- `src/frontend/` contains the Vite/React frontend for the public Pages site
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
