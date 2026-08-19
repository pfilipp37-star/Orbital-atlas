#!/bin/bash
set -e
cd "$(dirname "$0")"
PY_BIN="${PYTHON:-python3}"
if ! command -v "$PY_BIN" >/dev/null 2>&1; then
  echo "python3 not found. Please install Python 3.12+ first."
  read -n 1 -s -r -p "Press any key to exit..."
  exit 1
fi
if [ ! -d ".venv" ]; then
  "$PY_BIN" -m venv .venv
fi
source .venv/bin/activate
python -m pip install --upgrade pip >/dev/null
python -m pip install -r requirements.txt
python main.py
