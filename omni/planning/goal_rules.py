import re


OBJECT_ALIASES = {
    "chest": "chest",
    "СЃСѓРЅРґСѓРє": "chest",
    "oak_log": "oak_log",
    "РґСѓР±": "oak_log",
    "РґСѓР±РѕРІРѕРµ Р±СЂРµРІРЅРѕ": "oak_log",
    "РґСѓР±РѕРІС‹Р№ СЃС‚РІРѕР»": "oak_log",
    "birch_log": "birch_log",
    "Р±РµСЂС‘Р·Р°": "birch_log",
    "Р±РµСЂРµР·Р°": "birch_log",
    "Р±РµСЂС‘Р·РѕРІРѕРµ Р±СЂРµРІРЅРѕ": "birch_log",
    "Р±РµСЂРµР·РѕРІРѕРµ Р±СЂРµРІРЅРѕ": "birch_log",
    "spruce_log": "spruce_log",
    "РµР»СЊ": "spruce_log",
    "РµР»РѕРІРѕРµ Р±СЂРµРІРЅРѕ": "spruce_log",
    "crafting_table": "crafting_table",
    "РІРµСЂСЃС‚Р°Рє": "crafting_table",
    "furnace": "furnace",
    "РїРµС‡СЊ": "furnace",
}


def resolve_object_name(goal: str) -> str | None:
    lower = goal.lower()

    # РЎРЅР°С‡Р°Р»Р° РґР»РёРЅРЅС‹Рµ Р°Р»РёР°СЃС‹, С‡С‚РѕР±С‹ "РґСѓР±РѕРІРѕРµ Р±СЂРµРІРЅРѕ"
    # РїРѕР№РјР°Р»РѕСЃСЊ СЂР°РЅСЊС€Рµ, С‡РµРј РїСЂРѕСЃС‚Рѕ "РґСѓР±".
    for alias in sorted(OBJECT_ALIASES.keys(), key=len, reverse=True):
        if alias in lower:
            return OBJECT_ALIASES[alias]

    return None


def extract_seconds(goal: str, default: float = 3.0) -> float:
    lower = goal.lower()

    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(СЃРµРє|СЃРµРєСѓРЅРґ|seconds|second|s)", lower)
    if not match:
        return default

    value = match.group(1).replace(",", ".")
    return float(value)


def wants_remember(goal: str) -> bool:
    lower = goal.lower()

    return (
        "Р·Р°РїРѕРјРЅРё" in lower
        or "Р·Р°РїРѕРјРЅРёС‚СЊ" in lower
        or "РїРѕРјРЅРё" in lower
    )


def wants_report(goal: str) -> bool:
    lower = goal.lower()

    return (
        "СЃРєР°Р¶Рё" in lower
        or "СЃРѕРѕР±С‰Рё" in lower
        or "РЅР°РїРёС€Рё" in lower
    )


def wants_move_forward(goal: str) -> bool:
    lower = goal.lower()

    return (
        "РІРїРµСЂС‘Рґ" in lower
        or "РІРїРµСЂРµРґ" in lower
        or "РїСЂРѕР№РґРё" in lower
        or "РёРґРё" in lower
    )


def wants_dig(goal: str) -> bool:
    lower = goal.lower()

    return (
        "СЃР»РѕРјР°Р№" in lower
        or "СЃР»РѕРјР°С‚СЊ" in lower
        or "РґРѕР±СѓРґСЊ" in lower
        or "РґРѕР±С‹С‚СЊ" in lower
        or "СЂР°Р·Р±РµР№" in lower
        or "РІСЃРєРѕРїР°С‚СЊ" in lower
        or "РІСЃРєРѕРїР°Р№" in lower
    )


def wants_change_report(goal: str) -> bool:
    lower = goal.lower()

    return (
        "С‡С‚Рѕ РёР·РјРµРЅРёР»РѕСЃСЊ" in lower
        or "РёР·РјРµРЅРёР»РѕСЃСЊ" in lower
        or "СЃРєР°Р¶Рё" in lower
        or "СЃРѕРѕР±С‰Рё" in lower
        or "РЅР°РїРёС€Рё" in lower
    )


def wants_inventory_question(goal: str) -> bool:
    lower = goal.lower()

    return (
        "РёРЅРІРµРЅС‚Р°СЂ" in lower
        or "РІ СЂСѓРєРµ" in lower
        or ("Сѓ С‚РµР±СЏ РµСЃС‚СЊ" in lower)
        or ("РµСЃС‚СЊ Р»Рё Сѓ С‚РµР±СЏ" in lower)
        or ("СЃРєРѕР»СЊРєРѕ Сѓ С‚РµР±СЏ" in lower)
        or ("РІС‹Р±СЂР°РЅ" in lower and "СЃР»РѕС‚" in lower)
    )
