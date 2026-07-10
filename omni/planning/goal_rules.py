import re

from pymorphy3 import MorphAnalyzer


MORPH = MorphAnalyzer()

OBJECT_SURFACE_ALIASES = {
    "chest": "chest",
    "сундук": "chest",
    "oak_log": "oak_log",
    "дуб": "oak_log",
    "дубовое бревно": "oak_log",
    "дубовый ствол": "oak_log",
    "birch_log": "birch_log",
    "береза": "birch_log",
    "березовое бревно": "birch_log",
    "spruce_log": "spruce_log",
    "ель": "spruce_log",
    "еловое бревно": "spruce_log",
    "crafting_table": "crafting_table",
    "верстак": "crafting_table",
    "furnace": "furnace",
    "печь": "furnace",
    "печка": "furnace",
    "green_wool": "green_wool",
    "зеленая шерсть": "green_wool",
    "red_wool": "red_wool",
    "красная шерсть": "red_wool",
    "orange_wool": "orange_wool",
    "оранжевая шерсть": "orange_wool",
    "yellow_wool": "yellow_wool",
    "желтая шерсть": "yellow_wool",
    "light_blue_wool": "light_blue_wool",
    "голубая шерсть": "light_blue_wool",
    "blue_wool": "blue_wool",
    "синяя шерсть": "blue_wool",
    "purple_wool": "purple_wool",
    "фиолетовая шерсть": "purple_wool",
    "white_wool": "white_wool",
    "белая шерсть": "white_wool",
    "black_wool": "black_wool",
    "черная шерсть": "black_wool",
}


def _normalize_token(token: str) -> str:
    token = token.lower().replace("ё", "е")

    if re.fullmatch(r"[a-z0-9_]+", token):
        return token

    parsed = MORPH.parse(token)
    if not parsed:
        return token

    return parsed[0].normal_form.replace("ё", "е")


def normalize_text(text: str) -> str:
    tokens = re.findall(r"[a-zA-Z0-9_]+|[а-яА-ЯёЁ]+", text.lower())
    normalized = [_normalize_token(token) for token in tokens]
    return " ".join(normalized)


NORMALIZED_OBJECT_ALIASES = {
    normalize_text(alias): canonical
    for alias, canonical in OBJECT_SURFACE_ALIASES.items()
}


def _contains_any(goal: str, phrases: list[str]) -> bool:
    normalized_goal = normalize_text(goal)
    return any(normalize_text(phrase) in normalized_goal for phrase in phrases)


def resolve_object_name(goal: str) -> str | None:
    normalized_goal = normalize_text(goal)

    for alias in sorted(NORMALIZED_OBJECT_ALIASES.keys(), key=len, reverse=True):
        if alias in normalized_goal:
            return NORMALIZED_OBJECT_ALIASES[alias]

    return None


def extract_seconds(goal: str, default: float = 3.0) -> float:
    lower = goal.lower()

    match = re.search(r"(\d+(?:[.,]\d+)?)\s*(сек|секунд|seconds|second|s)", lower)
    if not match:
        return default

    value = match.group(1).replace(",", ".")
    return float(value)


def wants_remember(goal: str) -> bool:
    return _contains_any(goal, ["запомни", "запомнить", "помни"])


def wants_report(goal: str) -> bool:
    return _contains_any(goal, ["скажи", "сообщи", "напиши"])


def wants_move_forward(goal: str) -> bool:
    return _contains_any(goal, ["вперед", "пройди", "иди"])


def wants_dig(goal: str) -> bool:
    return _contains_any(goal, ["сломай", "сломать", "добудь", "добыть", "разбей", "вскопай", "вскопать"])


def wants_change_report(goal: str) -> bool:
    return _contains_any(goal, ["что изменилось", "изменилось", "скажи", "сообщи", "напиши"])


def wants_inventory_question(goal: str) -> bool:
    return _contains_any(
        goal,
        [
            "инвентарь",
            "в руке",
            "у тебя есть",
            "есть ли у тебя",
            "сколько у тебя",
            "выбран слот",
        ],
    )


def wants_select_item_in_hotbar(goal: str) -> bool:
    normalized_goal = normalize_text(goal)

    has_hand_phrase = "в рука" in normalized_goal
    has_hotbar_phrase = ("в hotbar" in normalized_goal) or ("в хотбар" in normalized_goal)
    has_select_verb = any(
        verb in normalized_goal
        for verb in [
            normalize_text("возьми"),
            normalize_text("выбери"),
            normalize_text("переключись"),
            normalize_text("держи"),
        ]
    )

    return (
        (has_hand_phrase and has_select_verb)
        or (has_hotbar_phrase and has_select_verb)
        or _contains_any(
            goal,
            [
                "переключись на",
                "выбери предмет",
            ],
        )
    )


def wants_select_hotbar_slot(goal: str) -> bool:
    return _contains_any(
        goal,
        [
            "выбери слот",
            "переключись на слот",
            "сделай активным слот",
        ],
    )
