from __future__ import annotations

import os
import sys
import traceback
from datetime import datetime
from pathlib import Path


def _log_dir() -> Path:
    if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
        path = Path(os.environ["LOCALAPPDATA"]) / "OrbitalAtlas" / "logs"
    else:
        path = Path(__file__).resolve().parent / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_crash(exc: BaseException) -> Path:
    path = _log_dir() / "crash.log"
    with path.open("a", encoding="utf-8") as f:
        f.write("\n" + "=" * 78 + "\n")
        f.write(datetime.now().isoformat(timespec="seconds") + "\n")
        f.write(f"Python: {sys.version}\n")
        f.write(f"Executable: {sys.executable}\n")
        f.write(f"CWD: {os.getcwd()}\n")
        traceback.print_exception(type(exc), exc, exc.__traceback__, file=f)
    return path


def main() -> int:
    if sys.version_info < (3, 12):
        raise RuntimeError("Orbital Atlas requires Python 3.12+ (Ursina 8.3.0).")
    try:
        from orbital_atlas.app import run
        run()
        return 0
    except BaseException as exc:
        path = _write_crash(exc)
        print(f"[CRASH] {type(exc).__name__}: {exc}")
        print(f"[CRASH] log: {path}")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
