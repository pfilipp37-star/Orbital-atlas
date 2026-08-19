from __future__ import annotations

LANGUAGES = ("en", "ru", "zh")
LANGUAGE_LABELS = {"en": "EN", "ru": "RU", "zh": "中文"}

STRINGS = {
    "en": {
        "legend":"BLUE: SATELLITE  •  ORANGE: ROCKET BODY  •  GRAY: DEBRIS  •  YELLOW: CITY",
        "help":"LMB: orbit Earth  •  wheel: zoom  •  click: object  •  F: free flight  •  G: focus object  •  R: Earth view  •  C: clear",
        "filters":"FILTERS","mode_free":"FREE","mode_orbit":"ORBIT","focus":"FOCUS","earth":"EARTH",
        "catalog_loading":"ORBITAL OBJECTS: loading…","catalog_none":"OBJECTS: 0  •  NO CATALOG — START_DEBUG.bat",
        "catalog_partial":"ORBITAL OBJECTS • PARTIAL CATALOG: {count}","catalog_max":"ORBITAL OBJECTS • MAX CELESTRAK: {count}","catalog_shown":"SHOWN {shown} / {total}",
        "filter_header":"ORBITAL FILTERS","country":"Country / owner","status":"Status","orbit":"Orbit","type":"Type","all":"All","apply":"APPLY","reset":"RESET","filters_reset":"Filters reset",
        "selection_type":"Type","selection_state":"Status","selection_launch":"Launch","selection_now":"Now","selection_height":"altitude","selection_metadata_missing":"SATCAT metadata unavailable",
        "launches_loading":"LAUNCHES: loading…","launches_none":"LAUNCHES: no data","next_launch":"NEXT LAUNCH: {rocket} • {provider} • {countdown}",
        "city_overhead_title":"SATELLITES ABOVE THE CITY (> {deg}°)","city_overhead_none":"Satellites above {deg}°: none right now","city_loading":"Orbital catalog is still loading…"
    },
    "ru": {
        "legend":"ГОЛУБОЙ: СПУТНИК  •  ОРАНЖЕВЫЙ: СТУПЕНЬ  •  СЕРЫЙ: ОБЛОМОК  •  ЖЁЛТЫЙ: ГОРОД",
        "help":"ЛКМ: вращать Землю  •  колесо: масштаб  •  клик: объект  •  F: свободный полёт  •  G: фокус  •  R: к Земле  •  C: очистить",
        "filters":"ФИЛЬТРЫ","mode_free":"FREE","mode_orbit":"ORBIT","focus":"ФОКУС","earth":"ЗЕМЛЯ",
        "catalog_loading":"ОРБИТАЛЬНЫЕ ОБЪЕКТЫ: загрузка…","catalog_none":"ОБЪЕКТЫ: 0  •  НЕТ КАТАЛОГА — START_DEBUG.bat",
        "catalog_partial":"ОРБИТАЛЬНЫЕ ОБЪЕКТЫ • ЧАСТИЧНЫЙ КАТАЛОГ: {count}","catalog_max":"ОРБИТАЛЬНЫЕ ОБЪЕКТЫ • MAX CELESTRAK: {count}","catalog_shown":"ПОКАЗАНО {shown} / {total}",
        "filter_header":"ФИЛЬТРЫ ОРБИТАЛЬНЫХ ОБЪЕКТОВ","country":"Страна / владелец","status":"Статус","orbit":"Орбита","type":"Тип","all":"Все","apply":"ПРИМЕНИТЬ","reset":"СБРОСИТЬ","filters_reset":"Фильтры сброшены",
        "selection_type":"Тип","selection_state":"Состояние","selection_launch":"Запуск","selection_now":"Сейчас","selection_height":"высота","selection_metadata_missing":"SATCAT-метаданные пока недоступны",
        "launches_loading":"ЗАПУСКИ: загрузка…","launches_none":"ЗАПУСКИ: данных нет","next_launch":"СЛЕД. ЗАПУСК: {rocket} • {provider} • {countdown}",
        "city_overhead_title":"СПУТНИКИ НАД ГОРОДОМ  (> {deg}°)","city_overhead_none":"Спутники выше {deg}°: сейчас не найдено","city_loading":"Орбитальный каталог ещё загружается…"
    },
    "zh": {
        "legend":"蓝色: 卫星  •  橙色: 火箭级段  •  灰色: 碎片  •  黄色: 城市",
        "help":"左键: 旋转地球  •  滚轮: 缩放  •  点击: 目标  •  F: 自由飞行  •  G: 聚焦目标  •  R: 回到地球  •  C: 清除",
        "filters":"筛选","mode_free":"自由","mode_orbit":"轨道","focus":"聚焦","earth":"地球",
        "catalog_loading":"轨道目标: 加载中…","catalog_none":"目标: 0  •  没有目录 — START_DEBUG.bat",
        "catalog_partial":"轨道目标 • 部分目录: {count}","catalog_max":"轨道目标 • MAX CELESTRAK: {count}","catalog_shown":"显示 {shown} / {total}",
        "filter_header":"轨道目标筛选","country":"国家 / 所有者","status":"状态","orbit":"轨道","type":"类型","all":"全部","apply":"应用","reset":"重置","filters_reset":"筛选已重置",
        "selection_type":"类型","selection_state":"状态","selection_launch":"发射","selection_now":"当前","selection_height":"高度","selection_metadata_missing":"SATCAT 元数据暂不可用",
        "launches_loading":"发射: 加载中…","launches_none":"发射: 无数据","next_launch":"下次发射: {rocket} • {provider} • {countdown}",
        "city_overhead_title":"城市上空的卫星 (> {deg}°)","city_overhead_none":"高于 {deg}° 的卫星: 当前没有","city_loading":"轨道目录仍在加载…"
    }
}

def tr(lang: str, key: str, **kwargs) -> str:
    language = lang if lang in STRINGS else "en"
    template = STRINGS[language].get(key, STRINGS["en"].get(key, key))
    return template.format(**kwargs)
