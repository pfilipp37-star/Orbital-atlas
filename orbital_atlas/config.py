from __future__ import annotations

from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"
PROJECT_CACHE_DIR = PROJECT_ROOT / "cache"
if os.name == "nt" and os.environ.get("LOCALAPPDATA"):
    CACHE_DIR = Path(os.environ["LOCALAPPDATA"]) / "OrbitalAtlas" / "cache"
else:
    CACHE_DIR = PROJECT_CACHE_DIR
CACHE_DIR.mkdir(parents=True, exist_ok=True)

APP_VERSION = "v0.1.0"

EARTH_EQUATORIAL_RADIUS = 2.6
EARTH_DIAMETER = EARTH_EQUATORIAL_RADIUS * 2.0
EARTH_LAT_SEGMENTS = 128
EARTH_LON_SEGMENTS = 256
LONGITUDE_OFFSET_DEG = 0.0
ALTITUDE_EXAGGERATION = 1.0
CAMERA_MIN_DISTANCE = 2.82
CAMERA_MAX_DISTANCE = 28.0
CAMERA_START_DISTANCE = 7.8
CAMERA_CITY_DISTANCE = 3.05
CAMERA_LAUNCH_DISTANCE = 3.1
CAMERA_DRAG_SENSITIVITY = 78.0
CAMERA_ZOOM_STEP = 0.38
CAMERA_MAX_PITCH_DEG = 86.0
CAMERA_INERTIA = 0.0
CAMERA_SHAKE_MAX = 0.04
CAMERA_SHAKE_DECAY = 3.8
STAR_COUNT = 1050
STAR_MIN_RADIUS = 24.0
STAR_MAX_RADIUS = 52.0
ISS_NORAD_ID = 25544
SATELLITE_LIMIT = 0
SATELLITE_UPDATE_INTERVAL = 0.8
SATELLITE_POINT_PIXELS = 1.05
SATELLITE_CLICK_RADIUS = 0.035
ORBIT_TRACK_SAMPLES = 360
ORBIT_TRACK_THICKNESS = 2.0
ORBIT_TRACK_REFRESH_SECONDS = 15.0
FOCUS_ANIMATION_SECONDS = 1.15
FOCUS_CAMERA_DISTANCE = 0.72
SELECTED_MIN_SCALE = 0.14
SELECTED_MAX_SCALE = 0.62
AUTO_LOD_DISTANCE = 1.10
AUTO_LOD_MAX_MODELS = 12
AUTO_LOD_MIN_SCALE = 0.04
AUTO_LOD_MAX_SCALE = 0.085
MINIATURE_POOL_SIZE = 36
CELESTRAK_MAXIMAL_GP_SOURCES = (
    ("active", "https://celestrak.org/NORAD/elements/gp.php?GROUP=active&FORMAT=CSV", "PAYLOAD"),
    ("analyst", "https://celestrak.org/NORAD/elements/gp.php?GROUP=analyst&FORMAT=CSV", "UNKNOWN"),
    ("last30", "https://celestrak.org/NORAD/elements/gp.php?GROUP=last-30-days&FORMAT=CSV", "UNKNOWN"),
    ("rocket_bodies", "https://celestrak.org/NORAD/elements/gp.php?NAME=R%2FB&FORMAT=CSV", "ROCKET BODY"),
    ("debris", "https://celestrak.org/NORAD/elements/gp.php?NAME=DEB&FORMAT=CSV", "DEBRIS"),
    ("decaying", "https://celestrak.org/NORAD/elements/gp.php?SPECIAL=DECAYING&FORMAT=CSV", "UNKNOWN"),
    ("gpz_plus", "https://celestrak.org/NORAD/elements/gp.php?SPECIAL=GPZ-PLUS&FORMAT=CSV", "UNKNOWN"),
    ("platforms", "https://celestrak.org/NORAD/elements/gp.php?NAME=PLAT&FORMAT=CSV", "UNKNOWN"),
    ("tle_new", "https://celestrak.org/NORAD/elements/gp.php?SPECIAL=TLE-NEW&FORMAT=CSV", "UNKNOWN"),
    ("stations", "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=CSV", "PAYLOAD"),
    ("visual", "https://celestrak.org/NORAD/elements/gp.php?GROUP=visual&FORMAT=CSV", "PAYLOAD"),
)
SATVISOR_ACTIVE_TLE_MIRROR_URL = "https://raw.githubusercontent.com/satvisorcom/satvisor-data/master/celestrak/tle/active.tle"
MIRROR_MAX_AGE_DAYS = 1.0
CELESTRAK_FALLBACK_GROUP_URLS = (
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=CSV",
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=visual&FORMAT=CSV",
    "https://celestrak.org/NORAD/elements/gp.php?GROUP=gps-ops&FORMAT=CSV",
)
TLE_MAX_AGE_DAYS = 2.0 / 24.0
TLE_DOWNLOAD_TIMEOUT_SECONDS = 35.0
SATCAT_MAXIMAL_SOURCES = (
    ("active", "https://celestrak.org/satcat/records.php?GROUP=active&FORMAT=CSV"),
    ("last30", "https://celestrak.org/satcat/records.php?GROUP=last-30-days&FORMAT=CSV"),
    ("rocket_bodies", "https://celestrak.org/satcat/records.php?NAME=R%2FB&FORMAT=CSV&ONORBIT=1"),
    ("debris", "https://celestrak.org/satcat/records.php?NAME=DEB&FORMAT=CSV&ONORBIT=1"),
    ("gpz_plus", "https://celestrak.org/satcat/records.php?SPECIAL=GPZ-PLUS&FORMAT=CSV"),
    ("platforms", "https://celestrak.org/satcat/records.php?NAME=PLAT&FORMAT=CSV&ONORBIT=1"),
    ("tle_new", "https://celestrak.org/satcat/records.php?SPECIAL=TLE-NEW&FORMAT=CSV"),
    ("visual", "https://celestrak.org/satcat/records.php?GROUP=visual&FORMAT=CSV"),
)
SATCAT_MAX_AGE_DAYS = 1.0
CITY_DATASET_MIN_POPULATION = 15000
CITY_MARKER_MIN_POPULATION = 1_000_000
CITY_MARKER_LIMIT = 320
CITY_MARKER_ALTITUDE_KM = 10.0
CITY_OVERHEAD_MIN_ELEVATION_DEG = 8.0
CITY_OVERHEAD_LIMIT = 12
CITY_OVERHEAD_REFRESH_SECONDS = 1.5
LAUNCH_LIBRARY_UPCOMING_URL = "https://ll.thespacedevs.com/2.3.0/launches/upcoming/?limit=48&mode=normal&ordering=net"
LAUNCH_CACHE_MAX_AGE_MINUTES = 15
LAUNCH_DOWNLOAD_TIMEOUT_SECONDS = 20
LAUNCH_MARKER_ALTITUDE_KM = 15.0
LAUNCH_SITE_LIMIT = 10
LAUNCH_TIMER_LABEL_LIMIT = 5
LAUNCH_ANIMATION_WINDOW_SECONDS = 180.0
LAUNCH_ANIMATION_DURATION_SECONDS = 150.0
LAUNCH_SHAKE_SECONDS = 8.0
LAUNCH_SMOKE_PARTICLES = 32
NASA_HD_STREAM_URL = "NASA_HD_STREAM_URL_M3U8_PLACEHOLDER"
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 360
VIDEO_PANEL_DISTANCE = 7.0
VIDEO_PANEL_RIGHT = 3.9
VIDEO_PANEL_UP = -1.8
VIDEO_PANEL_WIDTH = 3.0
VIDEO_PANEL_HEIGHT = VIDEO_PANEL_WIDTH * VIDEO_HEIGHT / VIDEO_WIDTH
VIDEO_OPEN_TIMEOUT_MS = 6000
VIDEO_READ_TIMEOUT_MS = 6000
