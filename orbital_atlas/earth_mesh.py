from __future__ import annotations

from ursina import Mesh, Vec2, Vec3

from .config import EARTH_LAT_SEGMENTS, EARTH_LON_SEGMENTS
from .geo import earth_surface_scene_xyz


def build_wgs84_earth_mesh(lat_segments: int = EARTH_LAT_SEGMENTS, lon_segments: int = EARTH_LON_SEGMENTS) -> Mesh:
    lat_segments = max(24, int(lat_segments))
    lon_segments = max(48, int(lon_segments))
    vertices: list[Vec3] = []
    uvs: list[Vec2] = []
    triangles: list[tuple[int, int, int]] = []
    for lat_i in range(lat_segments + 1):
        v = lat_i / lat_segments
        latitude = -90.0 + 180.0 * v
        for lon_i in range(lon_segments + 1):
            u = lon_i / lon_segments
            longitude = -180.0 + 360.0 * u
            vertices.append(Vec3(*earth_surface_scene_xyz(latitude, longitude)))
            uvs.append(Vec2(u, v))
    stride = lon_segments + 1
    for lat_i in range(lat_segments):
        for lon_i in range(lon_segments):
            a = lat_i * stride + lon_i
            b = a + 1
            c = a + stride
            d = c + 1
            triangles.append((a, c, b))
            triangles.append((b, c, d))
    return Mesh(vertices=vertices, triangles=triangles, uvs=uvs, static=True, mode="triangle")
