from orbital_atlas.i18n import LANGUAGES, STRINGS, tr


def test_supported_languages_have_core_ui_strings():
    for language in LANGUAGES:
        for key in ("filters", "focus", "earth", "catalog_loading", "next_launch"):
            assert key in STRINGS[language]
            assert tr(language, key, rocket="R", provider="P", countdown="T-0")
