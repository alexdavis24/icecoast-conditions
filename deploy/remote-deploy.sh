#!/usr/bin/env bash

set -euo pipefail

required_vars=(
  BACKEND_IMAGE
  BACKEND_PORT
  COMPOSE_FILE
  COMPOSE_PROJECT_NAME
  DEPLOY_ROOT
  FRONTEND_IMAGE
  FRONTEND_PORT
  GHCR_TOKEN
  GHCR_USERNAME
  POSTGRES_PASSWORD
)

for name in "${required_vars[@]}"; do
  if [[ -z "${!name:-}" ]]; then
    echo "Missing required variable: $name" >&2
    exit 1
  fi
done

POSTGRES_DB="${POSTGRES_DB:-icecoast}"
POSTGRES_USER="${POSTGRES_USER:-icecoast}"

mkdir -p "$DEPLOY_ROOT"

printf '%s' "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USERNAME" --password-stdin

env_file="$DEPLOY_ROOT/.env"
cat >"$env_file" <<EOF
FRONTEND_IMAGE=$FRONTEND_IMAGE
BACKEND_IMAGE=$BACKEND_IMAGE
FRONTEND_PORT=$FRONTEND_PORT
BACKEND_PORT=$BACKEND_PORT
POSTGRES_DB=$POSTGRES_DB
POSTGRES_USER=$POSTGRES_USER
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
EOF

docker compose \
  --project-name "$COMPOSE_PROJECT_NAME" \
  --env-file "$env_file" \
  -f "$COMPOSE_FILE" \
  pull

docker compose \
  --project-name "$COMPOSE_PROJECT_NAME" \
  --env-file "$env_file" \
  -f "$COMPOSE_FILE" \
  up -d
