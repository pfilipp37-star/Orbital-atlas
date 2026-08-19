from __future__ import annotations

import csv
import math
import os
import tempfile
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from sgp4.api import SatrecArray
from skyfield.api import EarthSatellite, Loader, wgs84
from skyfield.sgp4lib import theta_GMST1982

from .config import (
    CELESTRAK_FALLBACK_GROUP_URLS,
    CELESTRAK_MAXIMAL_GP_SOURCES,
    ISS_NORAD_ID,
    MIRROR_MAX_AGE_DAYS,
    SATELLITE_LIMIT,
    SATELLITE_UPDATE_INTERVAL,
    SATVISOR_ACTIVE_TLE_MIRROR_URL,
    TLE_DOWNLOAD_TIMEOUT_SECONDS,
    TLE_MAX_AGE_DAYS,
)
from .geo import GeodeticPoint, SCENE_UNITS_PER_KM, geodetic_to_scene_xyz


@dataclass(slots=True)
class OrbitCatalog:
    iss: object | None
    satellites: list[object]
    timescale: object
    source_status: str = "MAX"
    error_message: str = ""
    source_count: int = 0


@dataclass(frozen=True, slots=True)
class SatelliteSceneState:
    xyz: tuple[float, float, float]
    geodetic: GeodeticPoint


@dataclass(frozen=True, slots=True)
class SatelliteBatchSnapshot:
    xyz: np.ndarray
    generated_monotonic: float


def infer_object_type_from_name(name: str, hint: str = "UNKNOWN") -> str:
    upper = (name or "").upper()
    hint = (hint or "UNKNOWN").upper()
    if " DEB" in upper or upper.endswith("DEB") or "DEBRIS" in upper:
        return "DEBRIS"
    if "R/B" in upper or "ROCKET BODY" in upper:
        return "ROCKET BODY"
    return hint if hint in {"PAYLOAD", "ROCKET BODY", "DEBRIS"} else "UNKNOWN"


def satellite_object_type(satellite: object) -> str:
    return str(getattr(satellite, "_ow_object_type", "") or infer_object_type_from_name(satellite_display_name(satellite))).upper()


def satellite_catalog_number(satellite: object) -> int:
    try:
        return int(getattr(satellite, "_ow_norad_id", satellite.model.satnum))
    except Exception:
        return -1


def satellite_display_name(satellite: object) -> str:
    name = str(getattr(satellite, "name", "") or "").strip()
    if name:
        return name
    norad = satellite_catalog_number(satellite)
    return f"NORAD {norad}" if norad >= 0 else "Orbital object"


class SatelliteCatalogLoader:
    """Merge several public CelesTrak OMM/CSV feeds and de-duplicate by NORAD ID."""

    def __init__(self, cache_dir: str | Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.loader = Loader(str(self.cache_dir), verbose=False)
        self.ts = self.loader.timescale(builtin=True)

    def load(self, satellite_limit: int = SATELLITE_LIMIT, allow_network: bool = True) -> OrbitCatalog:
        merged: list[object] = []
        errors: list[str] = []
        loaded_sources = 0
        active_loaded = False

        for slug, url, hint in CELESTRAK_MAXIMAL_GP_SOURCES:
            path = self.cache_dir / f"gp_{slug}.csv"
            if allow_network and (not path.exists() or self._is_stale(path, TLE_MAX_AGE_DAYS)):
                try:
                    self._download_atomic(url, path)
                except Exception as exc:
                    errors.append(f"{slug}: {self._friendly_error(exc)}")
            rows = self._load_csv(path, hint) if path.exists() else []
            if rows:
                loaded_sources += 1
                merged.extend(rows)
                active_loaded |= slug == "active"
                print(f"[SAT] {slug}: {len(rows):,}")

        if not active_loaded:
            mirror = self.cache_dir / "active_satellites_mirror.tle"
            if allow_network and (not mirror.exists() or self._is_stale(mirror, MIRROR_MAX_AGE_DAYS)):
                try:
                    self._download_tle_atomic(SATVISOR_ACTIVE_TLE_MIRROR_URL, mirror)
                except Exception as exc:
                    errors.append(f"active mirror: {exc}")
            if mirror.exists():
                rows = self._load_tle(mirror, "PAYLOAD")
                if rows:
                    merged.extend(rows)
                    loaded_sources += 1

        if not merged and allow_network:
            for i, url in enumerate(CELESTRAK_FALLBACK_GROUP_URLS):
                path = self.cache_dir / f"fallback_{i}.csv"
                try:
                    if not path.exists() or self._is_stale(path, TLE_MAX_AGE_DAYS):
                        self._download_atomic(url, path)
                    merged.extend(self._load_csv(path, "PAYLOAD"))
                except Exception as exc:
                    errors.append(f"fallback {i}: {exc}")

        unique: dict[int, object] = {}
        anonymous: list[object] = []
        for sat in merged:
            norad = satellite_catalog_number(sat)
            if norad >= 0:
                unique.setdefault(norad, sat)
            else:
                anonymous.append(sat)
        satellites = list(unique.values()) + anonymous
        iss = unique.get(ISS_NORAD_ID)

        if satellite_limit > 0 and len(satellites) > satellite_limit:
            indices = np.linspace(0, len(satellites) - 1, satellite_limit, dtype=np.int64)
            satellites = [satellites[int(i)] for i in indices]
            if iss is not None and all(satellite_catalog_number(x) != ISS_NORAD_ID for x in satellites):
                satellites[-1] = iss

        if not satellites:
            status = "UNAVAILABLE"
        elif loaded_sources >= max(3, len(CELESTRAK_MAXIMAL_GP_SOURCES) - 2):
            status = "MAX"
        else:
            status = "PARTIAL"
        return OrbitCatalog(iss, satellites, self.ts, status, " | ".join(errors), loaded_sources)

    def _load_csv(self, path: Path, hint: str) -> list[object]:
        out: list[object] = []
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    try:
                        norad = int(row.get("NORAD_CAT_ID") or -1)
                        sat = EarthSatellite.from_omm(self.ts, row)
                        sat.name = (row.get("OBJECT_NAME") or f"NORAD {norad}").strip()
                        setattr(sat, "_ow_norad_id", norad)
                        setattr(sat, "_ow_object_type", infer_object_type_from_name(sat.name, hint))
                        out.append(sat)
                    except Exception:
                        continue
        except Exception as exc:
            print(f"[SAT] parse failed {path.name}: {exc}")
        return out

    def _load_tle(self, path: Path, hint: str) -> list[object]:
        out: list[object] = []
        lines = [x.strip() for x in path.read_text(encoding="utf-8", errors="ignore").splitlines() if x.strip()]
        i = 0
        while i + 2 < len(lines):
            name, l1, l2 = lines[i:i+3]
            if l1.startswith("1 ") and l2.startswith("2 "):
                try:
                    sat = EarthSatellite(l1, l2, name, self.ts)
                    setattr(sat, "_ow_object_type", infer_object_type_from_name(name, hint))
                    out.append(sat)
                except Exception:
                    pass
                i += 3
            else:
                i += 1
        return out

    @staticmethod
    def _is_stale(path: Path, max_age_days: float) -> bool:
        return not path.exists() or time.time() - path.stat().st_mtime >= max_age_days * 86400.0

    @staticmethod
    def _friendly_error(exc: Exception) -> str:
        if isinstance(exc, urllib.error.HTTPError):
            return f"HTTP {exc.code}"
        return str(exc)

    @staticmethod
    def _download_atomic(url: str, destination: Path) -> None:
        req = urllib.request.Request(url, headers={"User-Agent": "OrbitalAtlas/0.1", "Accept": "text/csv,text/plain,*/*;q=0.5"})
        with urllib.request.urlopen(req, timeout=TLE_DOWNLOAD_TIMEOUT_SECONDS) as response:
            payload = response.read()
        head = payload[:4096].decode("utf-8", errors="ignore")
        if "NORAD_CAT_ID" not in head or "OBJECT_NAME" not in head:
            raise ValueError("response was not OMM CSV")
        SatelliteCatalogLoader._atomic_write(payload, destination)

    @staticmethod
    def _download_tle_atomic(url: str, destination: Path) -> None:
        req = urllib.request.Request(url, headers={"User-Agent": "OrbitalAtlas/0.1"})
        with urllib.request.urlopen(req, timeout=TLE_DOWNLOAD_TIMEOUT_SECONDS) as response:
            payload = response.read()
        SatelliteCatalogLoader._atomic_write(payload, destination)

    @staticmethod
    def _atomic_write(payload: bytes, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=destination.name + ".", suffix=".tmp", dir=destination.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, destination)
        except Exception:
            try:
                os.unlink(temp_name)
            except OSError:
                pass
            raise


TLECatalogLoader = SatelliteCatalogLoader


def satellite_scene_state(satellite: object, time_value: object) -> SatelliteSceneState | None:
    try:
        geocentric = satellite.at(time_value)
        lat, lon = wgs84.latlon_of(geocentric)
        height_km = float(wgs84.height_of(geocentric).km)
        latitude, longitude = float(lat.degrees), float(lon.degrees)
        xyz = geodetic_to_scene_xyz(latitude, longitude, height_km)
        if xyz is None:
            return None
        return SatelliteSceneState(xyz, GeodeticPoint(latitude, longitude, height_km))
    except Exception:
        return None


def _batch_scene_xyz(satrec_array: SatrecArray, time_value: object) -> np.ndarray:
    whole = float(np.asarray(time_value.whole))
    frac = float(np.asarray(time_value.tai_fraction) - np.asarray(time_value._leap_seconds()) / 86400.0)
    errors, r_teme, _ = satrec_array.sgp4(np.asarray([whole]), np.asarray([frac]))
    errors = np.asarray(errors)[:, 0]
    r = np.asarray(r_teme)[:, 0, :]
    theta, _ = theta_GMST1982(whole, float(np.asarray(time_value.ut1_fraction)))
    c, s = math.cos(float(theta)), math.sin(float(theta))
    ex = c * r[:, 0] + s * r[:, 1]
    ey = -s * r[:, 0] + c * r[:, 1]
    ez = r[:, 2]
    xyz = np.column_stack((ey, ez, -ex)) * SCENE_UNITS_PER_KM
    xyz[(errors != 0) | ~np.isfinite(xyz).all(axis=1)] = np.nan
    return xyz


class SatellitePropagationWorker:
    def __init__(self, satellites: list[object], timescale: object, interval: float = SATELLITE_UPDATE_INTERVAL):
        self.satellites = satellites
        self.timescale = timescale
        self.interval = max(0.8, float(interval), len(satellites) / 30000.0)
        self._array = SatrecArray([sat.model for sat in satellites]) if satellites else None
        self._lock = threading.Lock()
        self._snapshot: SatelliteBatchSnapshot | None = None
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True, name="orbital-propagation")
    def start(self):
        if self._array is not None:
            self._thread.start()
    def stop(self):
        self._stop.set()
    def latest(self):
        with self._lock:
            return self._snapshot
    def _run(self):
        while not self._stop.is_set():
            started = time.monotonic()
            try:
                xyz = _batch_scene_xyz(self._array, self.timescale.now())
                with self._lock:
                    self._snapshot = SatelliteBatchSnapshot(xyz, time.monotonic())
            except Exception as exc:
                print(f"[SAT] propagation failed: {exc}")
            self._stop.wait(max(0.05, self.interval - (time.monotonic() - started)))


def satellite_orbit_period_minutes(satellite: object) -> float:
    try:
        mm = float(satellite.model.no_kozai)
        if mm > 0:
            return float(np.clip(math.tau / mm, 70.0, 2880.0))
    except Exception:
        pass
    return 100.0


def satellite_track_scene_xyz(satellite: object, timescale: object, samples: int = 300) -> list[tuple[float, float, float]]:
    samples = max(64, int(samples))
    period_minutes = satellite_orbit_period_minutes(satellite)
    now = timescale.now()
    whole = float(np.asarray(now.whole))
    frac0 = float(np.asarray(now.tai_fraction) - np.asarray(now._leap_seconds()) / 86400.0)
    theta, _ = theta_GMST1982(whole, float(np.asarray(now.ut1_fraction)))
    c, s = math.cos(float(theta)), math.sin(float(theta))
    points: list[tuple[float, float, float]] = []
    for offset in np.linspace(0.0, period_minutes / 1440.0, samples):
        jd, fr = whole, frac0 + float(offset)
        carry = math.floor(fr); jd += carry; fr -= carry
        err, r, _ = satellite.model.sgp4(jd, fr)
        if err:
            continue
        tx, ty, tz = map(float, r)
        ex, ey = c * tx + s * ty, -s * tx + c * ty
        points.append((ey * SCENE_UNITS_PER_KM, tz * SCENE_UNITS_PER_KM, -ex * SCENE_UNITS_PER_KM))
    if len(points) >= 3 and float(getattr(satellite.model, "ecco", 1.0)) <= 0.25:
        points[-1] = points[0]
    return points
