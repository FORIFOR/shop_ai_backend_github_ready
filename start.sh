#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r requirements.txt

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8080}"

exec uvicorn app.main:app --host "$HOST" --port "$PORT" --reload
