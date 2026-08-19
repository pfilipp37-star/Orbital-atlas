from __future__ import annotations

import argparse

from ursina import Ursina, camera, color, scene, window

from .config import APP_VERSION, NASA_HD_STREAM_URL, SATELLITE_LIMIT
from .scene import OrbitalAtlasScene
from .font_support import configure_multilingual_font


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Interactive 3D Earth-orbit explorer")
    parser.add_argument("--earth-texture", default=None, help="Path to a 2:1 equirectangular Earth texture.")
    parser.add_argument("--stream-url", default=NASA_HD_STREAM_URL, help="Direct HLS/M3U8 NASA/ISS live stream URL.")
    parser.add_argument("--no-video", action="store_true", help="Disable the live video panel.")
    parser.add_argument("--offline", action="store_true", help="Use cached orbital data only.")
    parser.add_argument("--limit-satellites", type=int, default=SATELLITE_LIMIT, help="Debug object limit. 0 means all loaded objects.")
    return parser


def run(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    print(f"[APP] Orbital Atlas {APP_VERSION}")

    app = Ursina(vsync=True)
    window.title = f"Orbital Atlas {APP_VERSION}"
    window.color = color.black
    window.borderless = False
    window.fullscreen = False

    try:
        scene.setLightOff(1)
    except Exception:
        pass

    camera.fov = 60
    configure_multilingual_font()

    if hasattr(window, "fps_counter"):
        window.fps_counter.enabled = False
    if hasattr(window, "exit_button"):
        window.exit_button.visible = True
    if hasattr(window, "cog_button"):
        window.cog_button.visible = False

    OrbitalAtlasScene(
        earth_texture=args.earth_texture,
        stream_url=args.stream_url,
        show_video=not args.no_video,
        satellite_limit=max(0, args.limit_satellites),
        allow_network=not args.offline,
    )
    app.run()
