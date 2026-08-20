#!/bin/bash
set -u

cd "$(dirname "$0")" || exit 1
printf '\033]0;Orbital Atlas\007'

VENV=".venv"
PY="$VENV/bin/python"

pause_on_error() {
  printf '\nPress Return to close...'
  read -r _
}

fail() {
  echo
  echo "Setup failed."
  echo "If you need details, run this file from Terminal:"
  echo "  ./START_MAC.command"
  pause_on_error
  exit 1
}

python_ok() {
  "$1" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,12) else 9)' >/dev/null 2>&1
}

# Reuse an existing project environment only when it is Python 3.12+.
if [ -x "$PY" ] && ! python_ok "$PY"; then
  echo "Existing .venv uses an older Python. Recreating it..."
  rm -rf "$VENV" || fail
fi

if [ ! -x "$PY" ]; then
  BASEPY=""

  if command -v python3.12 >/dev/null 2>&1 && python_ok "$(command -v python3.12)"; then
    BASEPY="$(command -v python3.12)"
  elif command -v python3 >/dev/null 2>&1 && python_ok "$(command -v python3)"; then
    BASEPY="$(command -v python3)"
  elif command -v python >/dev/null 2>&1 && python_ok "$(command -v python)"; then
    BASEPY="$(command -v python)"
  fi

  if [ -z "$BASEPY" ]; then
    echo "Python 3.12+ is required."
    echo "Install Python 3.12 or newer from python.org, then double-click START_MAC.command again."
    pause_on_error
    exit 12
  fi

  echo "Creating Orbital Atlas environment..."
  "$BASEPY" -m venv "$VENV" || fail
  "$PY" -m pip install --upgrade pip || fail
  "$PY" -m pip install -r requirements.txt || fail
fi

# Match START.bat behavior: repair missing dependencies automatically.
if ! "$PY" -c 'import ursina, skyfield, sgp4, cv2, numpy, PIL, geonamescache' >/dev/null 2>&1; then
  echo "Installing or repairing dependencies..."
  "$PY" -m pip install -r requirements.txt || fail
fi

echo "Starting Orbital Atlas..."
"$PY" main.py "$@"
STATUS=$?

if [ "$STATUS" -ne 0 ]; then
  echo
  echo "Orbital Atlas exited with error code $STATUS."
  if [ -f "logs/crash.log" ]; then
    echo "Crash log: $(pwd)/logs/crash.log"
  fi
  pause_on_error
fi

exit "$STATUS"
