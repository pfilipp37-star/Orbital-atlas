# Orbital Atlas

Orbital Atlas is an open-source interactive 3D Earth-orbit explorer built with Python, Ursina, Skyfield/SGP4 and OpenCV. It visualizes real satellites, rocket bodies, debris, orbital paths, launch sites and upcoming rocket launches using public space-data sources.

## Features

- Large merged CelesTrak GP/OMM catalog with NORAD deduplication
- Real-time SGP4 propagation
- Satellites, rocket bodies, debris and analyst objects
- Dedicated ISS 3D model and lightweight automatic 3D LOD
- Persistent 3D model for the selected object
- Selected-object orbit visualization
- WGS84 Earth with NASA Blue Marble texture
- Launch-site models with family-aware rocket visuals and countdown timers
- Launch events with flame, smoke and camera shake
- Smooth focus transitions and free-flight camera
- English UI with Russian and Simplified Chinese options
- Optional NASA/ISS HLS video panel through OpenCV
- Normal desktop application for Windows, macOS and Linux

## Quick start

Python 3.12+ is required.

### Windows

```bat
START.bat
```

For troubleshooting:

```bat
START_DEBUG.bat
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

On macOS, `RUN_MACOS.command` is also included.

## Controls

- **LMB drag** — orbit around Earth
- **Mouse wheel** — zoom
- **Click object** — select it
- **G / FOCUS** — focus the selected object
- **WASD + Q/E** — free flight
- **RMB drag** — free look
- **Shift** — faster flight
- **R / EARTH** — return to Earth
- **C** — clear selection

## Data sources

- CelesTrak — orbital elements and SATCAT metadata
- Skyfield + sgp4 — propagation
- NASA Blue Marble — Earth texture
- The Space Devs / Launch Library 2 — upcoming launches and launch pads

## NASA video

The stream URL is intentionally a placeholder. Provide a current direct HLS/M3U8 URL with:

```bash
python main.py --stream-url "https://example.com/live.m3u8"
```

## Tests

```bash
python -m pytest -q
```

## License

MIT. See [LICENSE](LICENSE).
