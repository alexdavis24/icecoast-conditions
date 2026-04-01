# icecoast-conditions

Local-first web app for tracking Northeast ski conditions and what is happening across the region.

## Intended shape

- `src/frontend/` will hold the React frontend
- `src/backend/` will hold the FastAPI backend
- `src/pipeline/` will hold Python workers that collect and shape data for Postgres
- Cloudflare will be used for local hosting and related edge infrastructure

This repository is currently a skeleton only. It does not implement any of the application pieces yet.
