from __future__ import annotations

from pathlib import Path
import sys


def configure_multilingual_font() -> str | None:
    """Use an installed system CJK font when available, without bundling fonts."""
    from ursina import Text, application

    candidates: list[Path]
    if sys.platform == "win32":
        candidates = [Path("C:/Windows/Fonts/msyh.ttc"), Path("C:/Windows/Fonts/msyhbd.ttc"), Path("C:/Windows/Fonts/simsun.ttc")]
    elif sys.platform == "darwin":
        candidates = [Path("/System/Library/Fonts/PingFang.ttc"), Path("/System/Library/Fonts/STHeiti Light.ttc"), Path("/Library/Fonts/Arial Unicode.ttf")]
    else:
        candidates = [Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"), Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]

    for path in candidates:
        if not path.exists():
            continue
        try:
            application.fonts_folder = path.parent
            Text.default_font = path.name
            print(f"[FONT] multilingual font: {path}")
            return str(path)
        except Exception as exc:
            print(f"[FONT] failed to configure {path}: {exc}")
    print("[FONT] no system CJK font found; English/Russian remain available")
    return None
