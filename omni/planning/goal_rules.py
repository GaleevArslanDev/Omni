import re


OBJECT_ALIASES = {
    "chest": "chest",
    "сундук": "chest",
    "oak_log": "oak_log",
    "дуб": "oak_log",
    "дубовое бревно": "oak_log",
    "дубовый ствол": "oak_log",
    "birch_log": "birch_log",
    "береза": "birch_log",
    "берёза": "birch_log",
    "березовое бревно": "birch_log",
    "берёзовое бревно": "birch_log",
    "spruce_log": "spruce_log",
    "ель": "spruce_log",
    "еловое бревно": "spruce_log",
    "crafting_table": "crafting_table",
    "верстак": "crafting_table",
    "furnace": "furnace",
    "печь": "furnace",
}


def resolve_object_name(goal: str) -> str | None:
    lower = goal.lower()

    # Сначала длинные алиасы, чтобы "дубовое бревно"
    # поймалось раньше, чем просто "дуб".
    for alias in sorted(OBJECT_ALIASES.keys(), key=len, reverse=True):
        if alias in lower:
            return OBJECT_ALIASES[alias]

    return None


def extract_seconds(goal: str, default: float = 3.0) -> float:
    lower = goal.lower()

    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(сек|секунд|seconds|second|s)", lower)
    if not match:
        return default

    value = match.group(1).replace(",", ".")
    return float(value)


def wants_remember(goal: str) -> bool:
    lower = goal.lower()

    return (
        "запомни" in lower
        or "запомнить" in lower
        or "помни" in lower
    )


def wants_report(goal: str) -> bool:
    lower = goal.lower()

    return (
        "скажи" in lower
        or "сообщи" in lower
        or "напиши" in lower
    )


def wants_move_forward(goal: str) -> bool:
    lower = goal.lower()

    return (
        "вперёд" in lower
        or "вперед" in lower
        or "пройди" in lower
        or "иди" in lower
    )


def wants_dig(goal: str) -> bool:
    lower = goal.lower()

    return (
        "сломай" in lower
        or "сломать" in lower
        or "добудь" in lower
        or "добыть" in lower
        or "разбей" in lower
        or "вскопать" in lower
        or "вскопай" in lower
    )


def wants_change_report(goal: str) -> bool:
    lower = goal.lower()

    return (
        "что изменилось" in lower
        or "изменилось" in lower
        or "скажи" in lower
        or "сообщи" in lower
        or "напиши" in lower
    )


def wants_inventory_question(goal: str) -> bool:
    lower = goal.lower()

    return (
        "инвентар" in lower
        or "в руке" in lower
        or ("у тебя есть" in lower)
        or ("есть ли у тебя" in lower)
        or ("сколько у тебя" in lower)
        or ("выбран" in lower and "слот" in lower)
    )
