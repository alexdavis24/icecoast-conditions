# Deploy Assets

This directory contains the assets GitHub Actions copies to the Ubuntu host before running a release deployment.

## Runtime model

- `vX.Y.Z-dev` tags deploy the development environment.
- `vX.Y.Z` tags deploy the production environment.
- Both environments run on the same host as separate Docker Compose projects.

## Host ports

- Production frontend: `3000`
- Development frontend: `3001`
- Production backend: `127.0.0.1:8000`
- Development backend: `127.0.0.1:8001`

## Caddy

Use distinct hostnames that point to the distinct frontend ports:

```caddy
icecoastnicecoast.com {
    reverse_proxy localhost:3000
}

www.icecoastnicecoast.com {
    reverse_proxy localhost:3000
}

dev.icecoastnicecoast.com {
    reverse_proxy localhost:3001
}
```

## Server prerequisites

- Docker Engine with the `docker compose` plugin installed
- Caddy already configured on the host
- The GitHub Actions workflow must have these secrets:
  - `GHCR_USERNAME`
  - `GHCR_TOKEN`
  - `SERVER_HOST`
  - `SERVER_USER`
  - `SERVER_SSH_KEY`
  - `POSTGRES_PASSWORD`
