#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env. Add a new Gemini API key there, then run this script again."
  exit 0
fi
python main.py