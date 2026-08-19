from __future__ import annotations

from pathlib import Path
import urllib.request

import numpy as np
from PIL import Image

from .config import ASSETS_DIR

NASA_BLUE_MARBLE_2048 = "https://svs.gsfc.nasa.gov/vis/a000000/a002900/a002915/bluemarble-2048.png"


def _validate_earth_map(path: Path) -> Path:
    try:
        with Image.open(path) as image:
            width, height = image.size
    except Exception as exc:
        raise ValueError(f"Cannot read Earth texture {path}: {exc}") from exc
    if width < 1024 or height < 512:
        raise ValueError(f"Earth texture is too small ({width}x{height}). Use at least 1024x512.")
    if abs(width / height - 2.0) > 0.02:
        raise ValueError(f"Earth texture must be 2:1 equirectangular, got {width}x{height}.")
    return path


def ensure_earth_texture(preferred: str | Path | None = None) -> Path:
    """Return a real NASA Blue Marble map, downloading it on first run if needed."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    if preferred:
        path = Path(preferred).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Custom Earth texture does not exist: {path}")
        return _validate_earth_map(path)

    for candidate in (ASSETS_DIR / "earth_day.png", ASSETS_DIR / "earth_day.jpg"):
        if candidate.exists():
            return _validate_earth_map(candidate)

    destination = ASSETS_DIR / "earth_day.png"
    temp = destination.with_suffix(".tmp")
    try:
        request = urllib.request.Request(NASA_BLUE_MARBLE_2048, headers={"User-Agent": "OrbitalAtlas/0.1"})
        with urllib.request.urlopen(request, timeout=30) as response, temp.open("wb") as out:
            out.write(response.read())
        temp.replace(destination)
        return _validate_earth_map(destination)
    except Exception as exc:
        temp.unlink(missing_ok=True)
        raise FileNotFoundError(
            "NASA Blue Marble texture is missing and automatic download failed. "
            "Pass --earth-texture PATH to a 2:1 equirectangular map."
        ) from exc


def ensure_atmosphere_glow_texture() -> Path:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    path = ASSETS_DIR / "atmosphere_glow.png"
    if path.exists():
        return path
    size = 512
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    cx = cy = (size - 1) / 2.0
    r = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (size / 2.0)
    rim = np.exp(-((r - 0.93) / 0.055) ** 2)
    rim *= np.clip((1.02 - r) / 0.08, 0.0, 1.0)
    alpha = np.uint8(np.clip(rim * 105.0, 0.0, 105.0))
    rgba = np.zeros((size, size, 4), dtype=np.uint8)
    rgba[..., 0] = 55
    rgba[..., 1] = 145
    rgba[..., 2] = 255
    rgba[..., 3] = alpha
    Image.fromarray(rgba, mode="RGBA").save(path)
    return path
