from __future__ import annotations

import json
import os
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import LAUNCH_CACHE_MAX_AGE_MINUTES, LAUNCH_DOWNLOAD_TIMEOUT_SECONDS, LAUNCH_LIBRARY_UPCOMING_URL


@dataclass(frozen=True, slots=True)
class LaunchEvent:
    launch_id: str
    name: str
    net: datetime
    latitude: float
    longitude: float
    pad_name: str
    location_name: str
    provider: str
    rocket: str
    status: str

    @property
    def seconds_until(self) -> float:
        return (self.net - datetime.now(timezone.utc)).total_seconds()


class UpcomingLaunchLoader:
    def __init__(self, cache_dir: str | Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_path = self.cache_dir / "upcoming_launches.json"

    def load(self, allow_network: bool = True) -> list[LaunchEvent]:
        if allow_network and (not self.cache_path.exists() or self._is_stale(self.cache_path)):
            try:
                self._download_atomic()
            except Exception as exc:
                print(f"[LAUNCH] refresh failed; using cache if available: {exc}")
        if not self.cache_path.exists(): return []
        try:
            return self._parse(json.loads(self.cache_path.read_text(encoding="utf-8")))
        except Exception as exc:
            print(f"[LAUNCH] parse failed: {exc}")
            return []

    @staticmethod
    def _is_stale(path: Path) -> bool:
        return max(0.0, time.time() - path.stat().st_mtime) >= LAUNCH_CACHE_MAX_AGE_MINUTES * 60.0

    def _download_atomic(self) -> None:
        req = urllib.request.Request(LAUNCH_LIBRARY_UPCOMING_URL, headers={"User-Agent": "OrbitalAtlas/0.1", "Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=LAUNCH_DOWNLOAD_TIMEOUT_SECONDS) as response:
            payload = response.read()
        parsed = json.loads(payload.decode("utf-8"))
        if not isinstance(parsed, dict) or "results" not in parsed:
            raise ValueError("Launch Library response did not contain results")
        fd, temp_name = tempfile.mkstemp(prefix="launches.", suffix=".tmp", dir=self.cache_dir)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload); handle.flush(); os.fsync(handle.fileno())
            os.replace(temp_name, self.cache_path)
        except Exception:
            try: os.unlink(temp_name)
            except OSError: pass
            raise

    @staticmethod
    def _parse(payload: dict) -> list[LaunchEvent]:
        out: list[LaunchEvent] = []
        for row in payload.get("results", []):
            try:
                pad = row.get("pad") or {}; lat = pad.get("latitude"); lon = pad.get("longitude")
                if lat is None or lon is None: continue
                net = datetime.fromisoformat(str(row.get("net") or "").replace("Z", "+00:00"))
                if net.tzinfo is None: net = net.replace(tzinfo=timezone.utc)
                provider = (row.get("launch_service_provider") or {}).get("name") or "Unknown provider"
                rocket_cfg = (row.get("rocket") or {}).get("configuration") or {}
                rocket = rocket_cfg.get("full_name") or rocket_cfg.get("name") or "Rocket"
                status = (row.get("status") or {}).get("name") or "Unknown"
                location = pad.get("location") or {}
                out.append(LaunchEvent(str(row.get("id") or ""), str(row.get("name") or rocket), net.astimezone(timezone.utc), float(lat), float(lon), str(pad.get("name") or "Launch pad"), str(location.get("name") or ""), str(provider), str(rocket), str(status)))
            except Exception:
                continue
        out.sort(key=lambda x: x.net)
        return out
