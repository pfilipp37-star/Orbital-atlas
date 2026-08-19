from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from ursina import Button, Entity, InputField, Text, camera, color

from .i18n import LANGUAGE_LABELS, tr

STATUS_OPTIONS = [
    "ALL", "Operational", "Nonoperational", "Partially operational",
    "Backup / standby", "Spare / awaiting activation", "Extended mission", "Unknown",
]
ORBIT_OPTIONS = ["ALL", "LEO", "MEO", "GEO", "HEO", "Unknown"]
TYPE_OPTIONS = ["ALL", "PAYLOAD", "ROCKET BODY", "DEBRIS", "UNKNOWN"]


@dataclass
class SearchChoice:
    kind: str
    title: str
    subtitle: str
    payload: object
    exact_key: str = ""


class SatelliteCatalogUI(Entity):
    """Minimal HUD: filters + language, without a permanent search bar."""

    def __init__(
        self,
        on_search_result: Callable[[int], None] | None = None,
        on_filter_change: Callable[[dict[str, str]], None] | None = None,
        external_search: Callable | None = None,
        on_external_result: Callable | None = None,
        on_language_change: Callable[[str], None] | None = None,
        language: str = "en",
    ):
        super().__init__(parent=camera.ui)
        self.on_filter_change = on_filter_change or (lambda _f: None)
        self.on_language_change = on_language_change or (lambda _l: None)
        self.language = language
        self._status_i = self._orbit_i = self._type_i = 0

        self.top_shell = Entity(parent=self, model="quad", position=(0.20, 0.456), scale=(0.57, 0.064), color=color.rgba32(4, 10, 17, 238))
        self.filter_button = Button(parent=self, text="", position=(0.05, 0.456), scale=(0.11, 0.04), color=color.rgba32(15, 35, 50, 255), text_color=color.white, on_click=self.toggle_filters)
        self.focus_hint = Text(parent=self, text="", position=(-0.22, 0.458), origin=(0.5, 0.5), scale=0.47, color=color.rgba32(167, 198, 223, 235))

        self.language_label = Text(parent=self, text="LANG", position=(0.26, 0.458), origin=(-0.5, 0.5), scale=0.42, color=color.rgba32(150, 184, 208, 240))
        self.lang_buttons: dict[str, Button] = {}
        for i, code in enumerate(("en", "ru", "zh")):
            b = Button(parent=self, text=LANGUAGE_LABELS[code], position=(0.34 + i * 0.075, 0.456), scale=(0.06, 0.037), color=color.rgba32(10, 24, 39, 255), text_color=color.rgba32(236, 243, 247, 255), on_click=lambda c=code: self.set_language(c))
            self.lang_buttons[code] = b

        self.feedback = Text(parent=self, text="", position=(-0.09, 0.418), origin=(0, 0.5), scale=0.42, color=color.rgba32(149, 178, 204, 220))

        self.filter_panel = Entity(parent=self, model="quad", position=(-0.69, 0.18), scale=(0.35, 0.43), color=color.rgba32(4, 12, 21, 248), enabled=False)
        self.filter_header = Text(parent=self.filter_panel, text="", x=-0.46, y=0.43, origin=(-0.5, 0), scale=1.65, color=color.rgba32(104, 188, 234, 255))
        self.country_label = Text(parent=self.filter_panel, text="", x=-0.46, y=0.27, origin=(-0.5, 0), scale=1.45, color=color.rgba32(160, 187, 207, 255))
        self.country_input = InputField(parent=self.filter_panel, default_value="", x=-0.02, y=0.14, scale=(0.82, 0.10), color=color.rgba32(9, 24, 37, 255), text_color=color.white)
        try:
            self.country_input.text_field.text_entity.scale *= 0.72
        except Exception:
            pass
        self.status_button = Button(parent=self.filter_panel, text="", y=-0.03, scale=(0.82, 0.10), color=color.rgba32(12, 34, 52, 255), on_click=self._cycle_status)
        self.orbit_button = Button(parent=self.filter_panel, text="", y=-0.17, scale=(0.82, 0.10), color=color.rgba32(12, 34, 52, 255), on_click=self._cycle_orbit)
        self.type_button = Button(parent=self.filter_panel, text="", y=-0.31, scale=(0.82, 0.10), color=color.rgba32(12, 34, 52, 255), on_click=self._cycle_type)
        self.apply_button = Button(parent=self.filter_panel, text="", y=-0.48, scale=(0.82, 0.105), color=color.rgba32(30, 119, 176, 255), on_click=self._emit_filter)
        self.reset_button = Button(parent=self.filter_panel, text="", y=-0.62, scale=(0.82, 0.10), color=color.rgba32(12, 34, 52, 255), on_click=self.reset_filters)

        self.language = language if language in LANGUAGE_LABELS else "en"
        self._sync_filter_labels()

    def set_catalog(self, metadata: dict[int, object], satellites: list[object]) -> None:
        return

    def toggle_filters(self) -> None:
        self.filter_panel.enabled = not self.filter_panel.enabled

    def _cycle_status(self) -> None:
        self._status_i = (self._status_i + 1) % len(STATUS_OPTIONS)
        self._sync_filter_labels()

    def _cycle_orbit(self) -> None:
        self._orbit_i = (self._orbit_i + 1) % len(ORBIT_OPTIONS)
        self._sync_filter_labels()

    def _cycle_type(self) -> None:
        self._type_i = (self._type_i + 1) % len(TYPE_OPTIONS)
        self._sync_filter_labels()

    def reset_filters(self) -> None:
        self._status_i = self._orbit_i = self._type_i = 0
        try:
            self.country_input.text = ""
        except Exception:
            pass
        self.feedback.text = tr(self.language, "filters_reset")
        self._sync_filter_labels()
        self._emit_filter()

    def current_filter(self) -> dict[str, str]:
        country = self.country_input.text.strip() if hasattr(self.country_input, "text") else ""
        return {
            "country": country or "ALL",
            "status": STATUS_OPTIONS[self._status_i],
            "orbit": ORBIT_OPTIONS[self._orbit_i],
            "type": TYPE_OPTIONS[self._type_i],
        }

    def _emit_filter(self) -> None:
        self.on_filter_change(self.current_filter())

    def _sync_filter_labels(self) -> None:
        lang = self.language
        self.filter_header.text = tr(lang, "filter_header")
        self.country_label.text = tr(lang, "country")
        self.filter_button.text = tr(lang, "filters")
        self.language_label.text = "LANG"
        self.focus_hint.text = ""
        all_label = tr(lang, "all")
        s = STATUS_OPTIONS[self._status_i]
        o = ORBIT_OPTIONS[self._orbit_i]
        t = TYPE_OPTIONS[self._type_i]
        self.status_button.text = f"{tr(lang, 'status')}: {all_label if s == 'ALL' else s}"
        self.orbit_button.text = f"{tr(lang, 'orbit')}: {all_label if o == 'ALL' else o}"
        type_label = {
            'ALL': all_label,
            'PAYLOAD': 'Payload' if lang == 'en' else ('Аппарат' if lang == 'ru' else '载荷'),
            'ROCKET BODY': 'Rocket body' if lang == 'en' else ('Ступень' if lang == 'ru' else '火箭级段'),
            'DEBRIS': 'Debris' if lang == 'en' else ('Обломок' if lang == 'ru' else '碎片'),
            'UNKNOWN': 'Unknown' if lang == 'en' else ('Неизвестно' if lang == 'ru' else '未知'),
        }[t]
        self.type_button.text = f"{tr(lang, 'type')}: {type_label}"
        self.apply_button.text = tr(lang, 'apply')
        self.reset_button.text = tr(lang, 'reset')
        for code, button in self.lang_buttons.items():
            button.color = color.rgba32(30, 119, 176, 255) if code == lang else color.rgba32(10, 24, 39, 255)

    def set_language(self, language: str) -> None:
        self.language = language if language in LANGUAGE_LABELS else 'en'
        self._sync_filter_labels()
        self.on_language_change(self.language)
