# Agents

This repository is being set up as a minimal monorepo-style skeleton for a Northeast ski conditions product.

Working context:

- Frontend: React
- Backend: FastAPI
- Data pipeline: Python workers that likely write to Postgres
- Deployment / local hosting direction: Cloudflare
- Frontend runs as a Vite app and proxies API requests to the backend in compose
- Keep the compose file and Dockerfiles aligned with the local development flow

Guidance for future work:

- Keep frontend, backend, and pipeline concerns separated by directory
- Prefer small, explicit interfaces between layers
- Avoid duplicating product description here; the README should stay the user-facing overview
