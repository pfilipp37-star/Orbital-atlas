from __future__ import annotations

import csv
import os
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from .config import SATCAT_MAXIMAL_SOURCES, SATCAT_MAX_AGE_DAYS, TLE_DOWNLOAD_TIMEOUT_SECONDS

STATUS_NAMES = {"+":"Operational","-":"Nonoperational","P":"Partially operational","B":"Backup / standby","S":"Spare / awaiting activation","X":"Extended mission","D":"Decayed","?":"Unknown","":"Unknown"}
COUNTRY_NAMES = {
    "US":"United States","USA":"United States","PRC":"China","CHN":"China","CIS":"Russia/CIS","RU":"Russia","RUS":"Russia","ESA":"ESA / Europe","EUME":"EUMETSAT / Europe","EU":"European Union","FR":"France","FRA":"France","UK":"United Kingdom","GB":"United Kingdom","GER":"Germany","DE":"Germany","IT":"Italy","ITA":"Italy","SPN":"Spain","ES":"Spain","JPN":"Japan","JP":"Japan","IND":"India","IN":"India","CAN":"Canada","CA":"Canada","BRAZ":"Brazil","BR":"Brazil","ISR":"Israel","IL":"Israel","KOR":"South Korea","SKOR":"South Korea","NKOR":"North Korea","AUS":"Australia","AU":"Australia","UAE":"United Arab Emirates","SAUD":"Saudi Arabia","TURK":"Türkiye","IRAN":"Iran","ARGN":"Argentina","MEX":"Mexico","NETH":"Netherlands","NOR":"Norway","SWED":"Sweden","FIN":"Finland","POL":"Poland","CZCH":"Czech Republic","UKR":"Ukraine","BEL":"Belgium","LUXE":"Luxembourg","ITSO":"International","ISS":"International","NATO":"NATO","ALG":"Algeria","ANG":"Angola","ARM":"Armenia","AZER":"Azerbaijan","BELA":"Belarus","BGD":"Bangladesh","BHR":"Bahrain","BOL":"Bolivia","BUL":"Bulgaria","CHLE":"Chile","COL":"Colombia","DEN":"Denmark","ECU":"Ecuador","EGYP":"Egypt","EST":"Estonia","ETH":"Ethiopia","GREC":"Greece","HUN":"Hungary","INDO":"Indonesia","IRL":"Ireland","KAZ":"Kazakhstan","KEN":"Kenya","LKA":"Sri Lanka","LTU":"Lithuania","MALA":"Malaysia","MEX":"Mexico","MNG":"Mongolia","NIG":"Nigeria","NPL":"Nepal","NZ":"New Zealand","PAKI":"Pakistan","PERU":"Peru","POR":"Portugal","QAT":"Qatar","ROC":"Taiwan","ROM":"Romania","RWA":"Rwanda","SAFR":"South Africa","SING":"Singapore","SVN":"Slovenia","SWTZ":"Switzerland","THAI":"Thailand","TUN":"Tunisia","URY":"Uruguay","VENZ":"Venezuela","VTNM":"Vietnam"}


def normalize_object_type(value: str | None, name: str = "") -> str:
    raw = (value or "").strip().upper(); upper_name = (name or "").upper()
    if raw in {"PAY","PAYLOAD","PLAT"}: return "PAYLOAD"
    if raw in {"R/B","RB","ROCKET BODY"}: return "ROCKET BODY"
    if raw in {"DEB","DEBRIS"}: return "DEBRIS"
    if "R/B" in upper_name: return "ROCKET BODY"
    if " DEB" in upper_name or upper_name.endswith("DEB"): return "DEBRIS"
    return "UNKNOWN"


@dataclass(frozen=True)
class SatelliteMetadata:
    norad_id: int
    name: str
    object_id: str = ""
    object_type: str = "UNKNOWN"
    status_code: str = "?"
    owner_code: str = ""
    launch_date: str = ""
    launch_site: str = ""
    decay_date: str = ""
    period_minutes: float | None = None
    inclination_deg: float | None = None
    apogee_km: float | None = None
    perigee_km: float | None = None

    @property
    def country(self) -> str:
        code = self.owner_code.strip().upper(); return COUNTRY_NAMES.get(code, code or "Unknown")
    @property
    def status(self) -> str:
        return STATUS_NAMES.get(self.status_code.strip().upper(), self.status_code or "Unknown")
    @property
    def orbit_class(self) -> str:
        apo, peri = self.apogee_km, self.perigee_km
        if apo is None and peri is None: return "Unknown"
        alt = max(v for v in (apo, peri) if v is not None)
        if alt < 2000: return "LEO"
        if 30000 <= alt <= 40000: return "GEO"
        if alt < 30000: return "MEO"
        return "HEO"
    @property
    def mission(self) -> str:
        n = self.name.upper()
        if self.object_type == "ROCKET BODY": return "Rocket stage / upper stage"
        if self.object_type == "DEBRIS": return "Tracked orbital debris"
        if self.norad_id == 25544 or "ISS" in n or "TIANGONG" in n or "CSS" in n: return "Crewed space station"
        if any(k in n for k in ("STARLINK","ONEWEB","IRIDIUM","GLOBALSTAR","INTELSAT","SES-","EUTELSAT","VIASAT")): return "Communications"
        if any(k in n for k in ("GPS","NAVSTAR","GALILEO","GLONASS","BEIDOU","BDS","QZS","NAVIC")): return "Navigation"
        if any(k in n for k in ("NOAA","GOES","METEOR","METOP","HIMAWARI","FENGYUN","COSMIC")): return "Weather / atmosphere"
        if any(k in n for k in ("LANDSAT","SENTINEL","WORLDVIEW","PLANET","SKYSAT","TERRA","AQUA","ICEYE","CAPELLA")): return "Earth observation"
        if any(k in n for k in ("HUBBLE","JWST","TELESCOPE","CHANDRA","SWIFT","FERMI","TESS")): return "Science / astronomy"
        return "Satellite / spacecraft"


def _float_or_none(value):
    try: return float(value) if value not in (None, "") else None
    except (TypeError, ValueError): return None


class SatcatMetadataLoader:
    def __init__(self, cache_dir: str | Path):
        self.cache_dir = Path(cache_dir); self.cache_dir.mkdir(parents=True, exist_ok=True)
    def load(self, allow_network: bool = True) -> dict[int, SatelliteMetadata]:
        merged = {}
        for slug, url in SATCAT_MAXIMAL_SOURCES:
            path = self.cache_dir / f"satcat_{slug}.csv"
            if allow_network and (not path.exists() or self._is_stale(path)):
                try: self._download_atomic(url, path); print(f"[SATCAT] refreshed {slug}")
                except Exception as exc: print(f"[SATCAT] {slug} refresh failed: {exc}")
            if path.exists():
                for norad, meta in self._parse(path).items(): merged.setdefault(norad, meta)
        print(f"[SATCAT] merged metadata: {len(merged):,}")
        return merged
    @staticmethod
    def _is_stale(path: Path) -> bool:
        return max(0.0, time.time() - path.stat().st_mtime) >= SATCAT_MAX_AGE_DAYS * 86400.0
    @staticmethod
    def _parse(path: Path):
        out = {}
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                for row in csv.DictReader(handle):
                    try: norad = int(row.get("NORAD_CAT_ID", ""))
                    except (ValueError, TypeError): continue
                    name = (row.get("OBJECT_NAME") or f"NORAD {norad}").strip()
                    out[norad] = SatelliteMetadata(norad, name, (row.get("OBJECT_ID") or "").strip(), normalize_object_type(row.get("OBJECT_TYPE"), name), (row.get("OPS_STATUS_CODE") or "?").strip(), (row.get("OWNER") or "").strip(), (row.get("LAUNCH_DATE") or "").strip(), (row.get("LAUNCH_SITE") or "").strip(), (row.get("DECAY_DATE") or "").strip(), _float_or_none(row.get("PERIOD")), _float_or_none(row.get("INCLINATION")), _float_or_none(row.get("APOGEE")), _float_or_none(row.get("PERIGEE")))
        except Exception as exc: print(f"[SATCAT] parse failed for {path.name}: {exc}")
        return out
    @staticmethod
    def _download_atomic(url: str, destination: Path) -> None:
        request = urllib.request.Request(url, headers={"User-Agent":"OrbitalAtlas/0.1","Accept":"text/csv,text/plain,*/*;q=0.5"})
        with urllib.request.urlopen(request, timeout=TLE_DOWNLOAD_TIMEOUT_SECONDS) as response: payload = response.read()
        head = payload[:2048].decode("utf-8", errors="ignore")
        if "NORAD_CAT_ID" not in head or "OBJECT_NAME" not in head: raise ValueError("SATCAT download did not look like CSV")
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=destination.name+".", suffix=".tmp", dir=destination.parent)
        try:
            with os.fdopen(fd,"wb") as handle: handle.write(payload); handle.flush(); os.fsync(handle.fileno())
            os.replace(tmp_name,destination)
        except Exception:
            try: os.unlink(tmp_name)
            except OSError: pass
            raise
