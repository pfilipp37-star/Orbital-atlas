from __future__ import annotations

from math import sqrt

from ursina import window


# Screen-space marker sizes in pixels. The old SatelliteLayer defaults are only
# 1.85-4.6 px for most objects, which is too small on dense/high-DPI displays.
_OUTER_POINT_PIXELS = {
    "TINY": 3.0,
    "SMALL": 4.5,
    "MEDIUM": 5.8,
    "LARGE": 7.2,
}

# Markers projected over the Earth already need to be slightly larger for
# contrast, so increase these more conservatively to avoid excessive clutter.
_FRONT_POINT_PIXELS = {
    "TINY": 5.5,
    "SMALL": 7.0,
    "MEDIUM": 8.8,
    "LARGE": 10.8,
}


def _display_scale() -> float:
    """Return a conservative high-DPI scale based on the current window height."""
    try:
        height = float(window.size.y)
    except Exception:
        return 1.0
    if height <= 0:
        return 1.0

    # Keep ordinary 720p/900p windows at the designed size, then scale gently
    # for Retina/1440p/4K framebuffers without turning dense debris into blobs.
    return max(1.0, min(1.35, sqrt(height / 900.0)))


def apply_satellite_point_style(layer) -> None:
    scale = _display_scale()

    for cls, (mesh, entity) in layer.layers.items():
        mesh.thickness = _OUTER_POINT_PIXELS[cls] * scale
        entity.texture = "circle"

    for cls, (mesh, entity) in layer.front_layers.items():
        mesh.thickness = _FRONT_POINT_PIXELS[cls] * scale
        entity.texture = "circle"
