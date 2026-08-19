from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np

from .config import CITY_DATASET_MIN_POPULATION
from .geo import geodetic_to_scene_xyz


@dataclass(frozen=True, slots=True)
class CityRecord:
    geoname_id: str
    name: str
    country: str
    country_code: str
    latitude: float
    longitude: float
    population: int

    @property
    def label(self) -> str:
        return f"{self.name}, {self.country}"


_FALLBACK = (
    CityRecord("f1", "Moscow", "Russia", "RU", 55.7558, 37.6173, 13_000_000),
    CityRecord("f2", "Saint Petersburg", "Russia", "RU", 59.9343, 30.3351, 5_600_000),
    CityRecord("f3", "Tokyo", "Japan", "JP", 35.6762, 139.6503, 14_000_000),
    CityRecord("f4", "New York City", "United States", "US", 40.7128, -74.0060, 8_300_000),
    CityRecord("f5", "London", "United Kingdom", "GB", 51.5074, -0.1278, 8_900_000),
    CityRecord("f6", "Paris", "France", "FR", 48.8566, 2.3522, 2_100_000),
    CityRecord("f7", "Beijing", "China", "CN", 39.9042, 116.4074, 21_500_000),
    CityRecord("f8", "Shanghai", "China", "CN", 31.2304, 121.4737, 24_800_000),
    CityRecord("f9", "Delhi", "India", "IN", 28.6139, 77.2090, 16_800_000),
    CityRecord("f10", "Dubai", "United Arab Emirates", "AE", 25.2048, 55.2708, 3_600_000),
    CityRecord("f11", "Sydney", "Australia", "AU", -33.8688, 151.2093, 5_300_000),
    CityRecord("f12", "São Paulo", "Brazil", "BR", -23.5505, -46.6333, 12_300_000),
)

_ALIASES = {
    "москва": "moscow", "питер": "saint petersburg", "санкт-петербург": "saint petersburg",
    "токио": "tokyo", "лондон": "london", "париж": "paris", "пекин": "beijing",
    "шанхай": "shanghai", "нью-йорк": "new york city",
}


class CityCatalog:
    def __init__(self, min_population: int = CITY_DATASET_MIN_POPULATION):
        self.cities: list[CityRecord] = []
        self._alternate_names: dict[str, tuple[str, ...]] = {}
        try:
            import geonamescache
            gc = geonamescache.GeonamesCache(min_city_population=min_population)
            countries = gc.get_countries()
            for geoname_id, row in gc.get_cities().items():
                try:
                    cc = str(row.get("countrycode") or "").upper()
                    country = str((countries.get(cc) or {}).get("name") or cc or "Unknown")
                    gid = str(geoname_id)
                    self.cities.append(CityRecord(gid, str(row.get("name") or "Unknown"), country, cc, float(row.get("latitude")), float(row.get("longitude")), int(row.get("population") or 0)))
                    alternates = row.get("alternatenames") or ()
                    if isinstance(alternates, str): alternates = [alternates]
                    self._alternate_names[gid] = tuple(str(v).casefold() for v in alternates if v)
                except Exception:
                    continue
        except Exception as exc:
            print(f"[CITY] geonamescache unavailable, using fallback: {exc}")
            self.cities = list(_FALLBACK)
        self.cities.sort(key=lambda c: c.population, reverse=True)
        print(f"[CITY] loaded {len(self.cities):,} cities")

    def major(self, min_population: int, limit: int) -> list[CityRecord]:
        return [c for c in self.cities if c.population >= int(min_population)][:max(1, int(limit))]

    def search(self, query: str, limit: int = 8) -> list[CityRecord]:
        q = _ALIASES.get(query.strip().casefold(), query.strip().casefold())
        if not q: return []
        def names(c: CityRecord): return (c.name.casefold(),) + self._alternate_names.get(c.geoname_id, ())
        exact = [c for c in self.cities if any(n == q for n in names(c))]
        starts = [c for c in self.cities if any(n.startswith(q) for n in names(c)) and c not in exact]
        contains = [c for c in self.cities if any(q in n for n in names(c)) and c not in exact and c not in starts]
        return (exact + starts + contains)[:limit]


def city_scene_xyz(city: CityRecord, altitude_km: float = 0.0) -> tuple[float, float, float]:
    xyz = geodetic_to_scene_xyz(city.latitude, city.longitude, altitude_km)
    assert xyz is not None
    return xyz


def satellites_above_city(city: CityRecord, satellite_xyz: np.ndarray, *, min_elevation_deg: float = 8.0, valid_mask: np.ndarray | None = None, limit: int = 12) -> list[tuple[int, float]]:
    if satellite_xyz is None or len(satellite_xyz) == 0: return []
    observer = np.asarray(city_scene_xyz(city, 0.0), dtype=np.float64)
    up = observer / max(1e-12, float(np.linalg.norm(observer)))
    delta = np.asarray(satellite_xyz, dtype=np.float64) - observer[None, :]
    ranges = np.linalg.norm(delta, axis=1)
    valid = np.isfinite(delta).all(axis=1) & np.isfinite(ranges) & (ranges > 1e-9)
    if valid_mask is not None and len(valid_mask) == len(valid): valid &= valid_mask
    sin_elevation = np.full(len(ranges), -1.0, dtype=np.float64)
    sin_elevation[valid] = (delta[valid] @ up) / ranges[valid]
    threshold = math.sin(math.radians(float(min_elevation_deg)))
    indices = np.flatnonzero(valid & (sin_elevation >= threshold))
    if not len(indices): return []
    elevations = np.degrees(np.arcsin(np.clip(sin_elevation[indices], -1.0, 1.0)))
    order = np.argsort(-elevations)
    return [(int(indices[i]), float(elevations[i])) for i in order[:max(1, int(limit))]]
