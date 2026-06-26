#!/usr/bin/env bash
# Create a local .env from .env.example with freshly generated local secrets.
# No usable credential is ever committed — they are generated here, on the dev's
# machine, into the gitignored .env.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="$ROOT/.env"

if [ -f "$ENV_FILE" ]; then
  echo ".env already exists — leaving it untouched."
  exit 0
fi

cp "$ROOT/.env.example" "$ENV_FILE"

gen() { LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c "${1:-32}"; }
pg_pass="$(gen 24)"
secret_key="$(gen 48)"
identity_key="$(gen 48)"

# In-place edit (GNU/BSD compatible). '|' delimiter avoids clashes with URLs.
sed -i.bak \
  -e "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=${pg_pass}|" \
  -e "s|^DATABASE_URL=.*|DATABASE_URL=postgresql+psycopg://scintia:${pg_pass}@postgres:5432/scintia|" \
  -e "s|^SECRET_KEY=.*|SECRET_KEY=${secret_key}|" \
  -e "s|^IDENTITY_ENCRYPTION_KEY=.*|IDENTITY_ENCRYPTION_KEY=${identity_key}|" \
  "$ENV_FILE"
rm -f "$ENV_FILE.bak"

echo "Created .env with generated local secrets (DB password, SECRET_KEY, IDENTITY_ENCRYPTION_KEY)."
echo "ANTHROPIC_API_KEY is left empty — set it when report generation is wired."
