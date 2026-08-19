from __future__ import annotations

import math
from dataclasses import dataclass

from .config import ALTITUDE_EXAGGERATION, EARTH_EQUATORIAL_RADIUS, LONGITUDE_OFFSET_DEG

WGS84_A_KM = 6378.137
WGS84_INV_F = 298.257223563
WGS84_F = 1.0 / WGS84_INV_F
WGS84_B_KM = WGS84_A_KM * (1.0 - WGS84_F)
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)
SCENE_UNITS_PER_KM = EARTH_EQUATORIAL_RADIUS / WGS84_A_KM
EARTH_POLAR_RADIUS_SCENE = WGS84_B_KM * SCENE_UNITS_PER_KM

@dataclass(frozen=True, slots=True)
class GeodeticPoint:
    latitude_deg: float
    longitude_deg: float
    altitude_km: float

def geodetic_to_scene_xyz(latitude_deg: float, longitude_deg: float, altitude_km: float = 0.0, *, exaggerate_altitude: bool = True) -> tuple[float, float, float] | None:
    values = (latitude_deg, longitude_deg, altitude_km)
    if not all(math.isfinite(float(v)) for v in values):
        return None
    lat = math.radians(float(latitude_deg))
    lon = math.radians(float(longitude_deg) + LONGITUDE_OFFSET_DEG)
    h_km = max(float(altitude_km), 0.0)
    if exaggerate_altitude:
        h_km *= ALTITUDE_EXAGGERATION
    sin_lat, cos_lat = math.sin(lat), math.cos(lat)
    sin_lon, cos_lon = math.sin(lon), math.cos(lon)
    prime_vertical_radius = WGS84_A_KM / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    ecef_x = (prime_vertical_radius + h_km) * cos_lat * cos_lon
    ecef_y = (prime_vertical_radius + h_km) * cos_lat * sin_lon
    ecef_z = (prime_vertical_radius * (1.0 - WGS84_E2) + h_km) * sin_lat
    return ecef_y * SCENE_UNITS_PER_KM, ecef_z * SCENE_UNITS_PER_KM, -ecef_x * SCENE_UNITS_PER_KM

def earth_surface_scene_xyz(latitude_deg: float, longitude_deg: float) -> tuple[float, float, float]:
    xyz = geodetic_to_scene_xyz(latitude_deg, longitude_deg, 0.0, exaggerate_altitude=False)
    assert xyz is not None
    return xyz

def segment_intersects_wgs84_ellipsoid(start, end, *, equatorial_radius: float = EARTH_EQUATORIAL_RADIUS, polar_radius: float = EARTH_POLAR_RADIUS_SCENE, endpoint_margin: float = 1e-4) -> bool:
    sx, sy, sz = map(float, start); ex, ey, ez = map(float, end)
    dx, dy, dz = ex - sx, ey - sy, ez - sz
    a2 = equatorial_radius * equatorial_radius; b2 = polar_radius * polar_radius
    qa = (dx*dx + dz*dz)/a2 + (dy*dy)/b2
    qb = 2.0*((sx*dx + sz*dz)/a2 + (sy*dy)/b2)
    qc = (sx*sx + sz*sz)/a2 + (sy*sy)/b2 - 1.0
    if qa <= 1e-12: return False
    disc = qb*qb - 4.0*qa*qc
    if disc < 0.0: return False
    root = math.sqrt(disc); inv = 0.5/qa
    t1, t2 = (-qb-root)*inv, (-qb+root)*inv
    return (endpoint_margin < t1 < 1.0-endpoint_margin) or (endpoint_margin < t2 < 1.0-endpoint_margin)

def visible_points_from_camera_mask(camera_xyz, points_xyz, *, equatorial_radius: float = EARTH_EQUATORIAL_RADIUS, polar_radius: float = EARTH_POLAR_RADIUS_SCENE):
    import numpy as np
    pts = np.asarray(points_xyz, dtype=np.float64)
    if pts.ndim != 2 or pts.shape[1] != 3: return np.zeros(len(pts), dtype=bool)
    cam = np.asarray(camera_xyz, dtype=np.float64).reshape(3)
    valid = np.isfinite(pts).all(axis=1); out = valid.copy()
    if not valid.any(): return out
    scale = np.asarray([equatorial_radius, polar_radius, equatorial_radius], dtype=np.float64)
    c = cam/scale; p = pts/scale; d = p-c[None,:]
    qa = np.einsum("ij,ij->i", d, d); qb = 2.0*np.einsum("ij,j->i", d, c); qc = float(np.dot(c,c)-1.0)
    disc = qb*qb - 4.0*qa*qc; hit = (qa>1e-12)&(disc>=0.0)&valid; idx = np.flatnonzero(hit)
    if len(idx):
        root = np.sqrt(np.maximum(disc[idx],0.0)); denom = 2.0*qa[idx]
        t1 = (-qb[idx]-root)/denom; t2 = (-qb[idx]+root)/denom
        blocked = ((t1>1e-5)&(t1<0.99999))|((t2>1e-5)&(t2<0.99999)); out[idx[blocked]] = False
    return out
