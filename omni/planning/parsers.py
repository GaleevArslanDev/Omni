import re

from omni.planning.goal_rules import (
    extract_coordinates,
    extract_seconds,
    normalize_text,
    resolve_object_name,
    wants_change_report,
    wants_dig,
    wants_move_forward,
    wants_move_to_coordinates,
    wants_place_block,
    wants_remember,
    wants_report,
    wants_select_hotbar_slot,
    wants_select_item_in_hotbar,
)
from omni.planning.task_plan import TaskPlan, TaskStep


ENTITY_SURFACE_ALIASES = {
    "cow": "cow",
    "корова": "cow",
    "sheep": "sheep",
    "овца": "sheep",
    "pig": "pig",
    "свинья": "pig",
    "chicken": "chicken",
    "курица": "chicken",
    "zombie": "zombie",
    "зомби": "zombie",
    "skeleton": "skeleton",
    "скелет": "skeleton",
    "creeper": "creeper",
    "крипер": "creeper",
    "spider": "spider",
    "паук": "spider",
    "villager": "villager",
    "житель": "villager",
    "деревенский житель": "villager",
    "wandering_trader": "wandering_trader",
    "странствующий торговец": "wandering_trader",
    "boat": "boat",
    "лодка": "boat",
    "minecart": "minecart",
    "вагонетка": "minecart",
}

NORMALIZED_ENTITY_ALIASES = {
    normalize_text(alias): canonical
    for alias, canonical in ENTITY_SURFACE_ALIASES.items()
}

ATTITUDE_ALIASES = {
    "hostile": [
        "hostile",
        "hostile mobs",
        "враждебный",
        "враждебные",
        "враждебные мобы",
        "монстры",
        "опасные мобы",
    ],
    "neutral": [
        "neutral",
        "нейтральные",
        "нейтральные мобы",
    ],
    "friendly": [
        "friendly",
        "passive",
        "friendly mobs",
        "пассивные",
        "мирные",
        "дружелюбные",
        "животные",
    ],
    "utility": [
        "utility",
        "npc",
        "utility entities",
        "торговцы",
        "полезные",
    ],
}


def _resolve_entity_name(goal: str) -> str | None:
    normalized_goal = normalize_text(goal)

    for alias in sorted(NORMALIZED_ENTITY_ALIASES.keys(), key=len, reverse=True):
        if alias in normalized_goal:
            return NORMALIZED_ENTITY_ALIASES[alias]

    return None


def _resolve_entity_attitude(goal: str) -> str | None:
    normalized_goal = normalize_text(goal)

    for attitude, aliases in ATTITUDE_ALIASES.items():
        for alias in aliases:
            if normalize_text(alias) in normalized_goal:
                return attitude

    return None


def _contains_phrase(goal: str, phrases: list[str]) -> bool:
    normalized_goal = normalize_text(goal)
    return any(normalize_text(phrase) in normalized_goal for phrase in phrases)


def _mentions_nearby_scope(goal: str) -> bool:
    return _contains_phrase(
        goal,
        [
            "рядом",
            "поблизости",
            "вокруг",
            "nearby",
            "around",
            "near me",
        ],
    )


def _mentions_entity_scope(goal: str) -> bool:
    return _contains_phrase(
        goal,
        [
            "сущности",
            "сущность",
            "мобы",
            "моб",
            "entities",
            "entity",
            "mobs",
            "mob",
        ],
    )


def _mentions_count_question(goal: str) -> bool:
    return _contains_phrase(goal, ["сколько", "how many"])


def _mentions_has_question(goal: str) -> bool:
    return _contains_phrase(
        goal,
        [
            "есть ли",
            "есть",
            "is there",
            "are there",
        ],
    )


def _mentions_summary_question(goal: str) -> bool:
    return _contains_phrase(
        goal,
        [
            "какие",
            "кто",
            "что",
            "what",
            "which",
        ],
    )


def _mentions_dropped_items_scope(goal: str) -> bool:
    return _contains_phrase(
        goal,
        [
            "на земле",
            "валяется",
            "лежащие предметы",
            "лежащие вещи",
            "dropped item",
            "dropped items",
            "ground item",
            "ground items",
        ],
    )


def _mentions_vehicles_scope(goal: str) -> bool:
    return _contains_phrase(
        goal,
        [
            "лодка",
            "лодки",
            "вагонетка",
            "вагонетки",
            "vehicle",
            "vehicles",
            "transport",
        ],
    )


def try_parse_nearby_entity_report(goal: str) -> TaskPlan | None:
    normalized_goal = normalize_text(goal)

    question_mode = None
    if _mentions_count_question(goal):
        question_mode = "count"
    elif _mentions_has_question(goal):
        question_mode = "has"
    elif _mentions_summary_question(goal):
        question_mode = "summary"

    if question_mode is None:
        return None

    if "у тебя" in normalized_goal or "инвентар" in normalized_goal:
        return None

    entity_name = _resolve_entity_name(goal)
    attitude = _resolve_entity_attitude(goal)
    item_name = resolve_object_name(goal)

    has_entity_context = any(
        [
            _mentions_nearby_scope(goal),
            _mentions_entity_scope(goal),
            _mentions_dropped_items_scope(goal),
            _mentions_vehicles_scope(goal),
            entity_name is not None,
            attitude is not None,
        ]
    )
    if not has_entity_context:
        return None

    category = "nearby"
    target_name = None

    if _mentions_dropped_items_scope(goal):
        category = "dropped_items"
        target_name = item_name
    elif _mentions_vehicles_scope(goal) or entity_name in {"boat", "minecart"}:
        category = "vehicles"
        target_name = entity_name
    else:
        target_name = entity_name

    if question_mode == "count":
        if category == "nearby" and attitude is not None and target_name is None:
            mode = "count_attitude"
        else:
            mode = "count_name"
    elif question_mode == "has":
        if category == "nearby" and attitude is not None and target_name is None:
            mode = "has_attitude"
        else:
            mode = "has_name"
    else:
        mode = "summary"

    if mode in {"has_name", "count_name"} and target_name is None:
        return None

    arguments = {
        "category": category,
        "mode": mode,
    }
    if target_name is not None:
        arguments["target_name"] = target_name
    if attitude is not None:
        arguments["attitude"] = attitude

    return TaskPlan(
        goal=goal,
        steps=[
            TaskStep(
                id="report_nearby_entities",
                kind="use_tool",
                args={
                    "tool": "report_nearby_entities",
                    "arguments": arguments,
                },
            )
        ],
    )


def try_parse_move_to_coordinates(goal: str) -> TaskPlan | None:
    if not wants_move_to_coordinates(goal):
        return None

    coordinates = extract_coordinates(goal)
    if coordinates is None:
        return None

    x, y, z = coordinates

    return TaskPlan(
        goal=goal,
        steps=[
            TaskStep(
                id="move_to_coordinates",
                kind="use_tool",
                args={
                    "tool": "move_to_coordinates",
                    "arguments": {
                        "x": x,
                        "y": y,
                        "z": z,
                    },
                },
            )
        ],
    )


def try_parse_select_and_place_block(goal: str) -> TaskPlan | None:
    if not wants_place_block(goal):
        return None

    target_name = resolve_object_name(goal)
    if target_name is None:
        return None

    return TaskPlan(
        goal=goal,
        steps=[
            TaskStep(
                id="select_item_for_placement",
                kind="use_tool",
                args={
                    "tool": "select_item_in_hotbar",
                    "arguments": {
                        "target_item_name": target_name,
                    },
                },
            ),
            TaskStep(
                id="place_selected_block",
                kind="use_tool",
                args={
                    "tool": "place_block_at_cursor",
                    "arguments": {
                        "face": "top",
                        "expected_item_name": target_name,
                    },
                },
            ),
        ],
    )


def try_parse_place_block_from_hand(goal: str) -> TaskPlan | None:
    if not wants_place_block(goal):
        return None

    target_name = resolve_object_name(goal)
    if target_name is not None:
        return None

    return TaskPlan(
        goal=goal,
        steps=[
            TaskStep(
                id="place_block_from_hand",
                kind="use_tool",
                args={
                    "tool": "place_block_at_cursor",
                    "arguments": {
                        "face": "top",
                    },
                },
            )
        ],
    )


def try_parse_remember_move_report(goal: str) -> TaskPlan | None:
    target_name = resolve_object_name(goal)

    if target_name is None:
        return None

    if not wants_remember(goal):
        return None

    steps: list[TaskStep] = [
        TaskStep(
            id="remember_target_location",
            kind="remember_object_location",
            args={
                "target_name": target_name,
            },
        )
    ]

    if wants_move_forward(goal):
        secs = extract_seconds(goal, default=3.0)

        steps.append(
            TaskStep(
                id="move_forward_once",
                kind="use_tool",
                args={
                    "tool": "move_forward",
                    "arguments": {
                        "secs": secs,
                    },
                },
            )
        )

    if wants_report(goal):
        steps.append(
            TaskStep(
                id="report_target_location",
                kind="report_remembered_location",
                args={
                    "target_name": target_name,
                },
            )
        )

    return TaskPlan(
        goal=goal,
        steps=steps,
    )


def try_parse_dig_object(goal: str) -> TaskPlan | None:
    target_name = resolve_object_name(goal)

    if target_name is None:
        return None

    if not wants_dig(goal):
        return None

    steps: list[TaskStep] = [
        TaskStep(
            id="look_at_target",
            kind="use_tool",
            args={
                "tool": "look_at_nearest",
                "arguments": {
                    "block_name": target_name,
                },
            },
        ),
        TaskStep(
            id="dig_target",
            kind="use_tool",
            args={
                "tool": "dig_block_at_cursor",
                "arguments": {
                    "expected_name": target_name,
                },
            },
        ),
    ]

    if wants_change_report(goal):
        steps.append(
            TaskStep(
                id="report_change",
                kind="report_observation_diff",
                args={
                    "target_name": target_name,
                },
            )
        )

    return TaskPlan(
        goal=goal,
        steps=steps,
    )


def try_parse_agent_state_report(goal: str) -> TaskPlan | None:
    lower = goal.lower()

    asks_self_state = (
        "здоров" in lower
        or "health" in lower
        or "hp" in lower
        or "сытост" in lower
        or "food" in lower
        or "голод" in lower
        or "координат" in lower
        or "позици" in lower
        or "где ты" in lower
        or "поворот" in lower
        or "yaw" in lower
        or "pitch" in lower
        or ("выбран" in lower and "слот" in lower)
        or "в руке" in lower
        or "инвентар" in lower
        or "у тебя есть" in lower
        or "есть ли у тебя" in lower
        or "сколько у тебя" in lower
    )

    if not asks_self_state:
        return None

    def make_plan(step_id: str, field: str, item_name: str | None = None) -> TaskPlan:
        args = {
            "tool": "report_agent_state",
            "arguments": {
                "field": field,
            },
        }
        if item_name is not None:
            args["arguments"]["item_name"] = item_name

        return TaskPlan(
            goal=goal,
            steps=[
                TaskStep(
                    id=step_id,
                    kind="use_tool",
                    args=args,
                )
            ],
        )

    if "здоров" in lower or "health" in lower or "hp" in lower:
        return make_plan("report_health", "health")

    if "сытост" in lower or "food" in lower or "голод" in lower:
        return make_plan("report_food", "food")

    if "где ты" in lower or "координат" in lower or "позици" in lower:
        return make_plan("report_position", "position")

    if "поворот" in lower or "yaw" in lower or "pitch" in lower:
        return make_plan("report_rotation", "rotation")

    if "в руке" in lower:
        return make_plan("report_main_hand", "main_hand")

    if "выбран" in lower and "слот" in lower:
        return make_plan("report_selected_slot", "selected_slot")

    if "что у тебя в инвентаре" in lower or "что в инвентаре" in lower:
        return make_plan("report_inventory_summary", "inventory_summary")

    item_name = resolve_object_name(goal)

    if item_name is not None:
        if "сколько у тебя" in lower or ("сколько" in lower and "в инвентаре" in lower):
            return make_plan("report_inventory_count_item", "inventory_count_item", item_name)

        if "у тебя есть" in lower or "есть ли у тебя" in lower:
            return make_plan("report_inventory_has_item", "inventory_has_item", item_name)

    return None


def try_parse_select_item_if_present(goal: str) -> TaskPlan | None:
    lower = goal.lower().replace("ё", "е")
    target_name = resolve_object_name(goal)

    if target_name is None:
        return None

    mentions_condition = (
        "если" in lower
        and ("если у тебя есть" in lower or "если у тебя нет" in lower or "если у тебя не" in lower)
    )
    mentions_hold_request = wants_select_item_in_hotbar(goal)

    if not mentions_condition or not mentions_hold_request:
        return None

    return TaskPlan(
        goal=goal,
        steps=[
            TaskStep(
                id="select_item_if_present",
                kind="select_item_in_hotbar_or_say_missing",
                args={
                    "target_item_name": target_name,
                },
            )
        ],
    )


def try_parse_select_item_in_hotbar(goal: str) -> TaskPlan | None:
    if not wants_select_item_in_hotbar(goal):
        return None

    target_name = resolve_object_name(goal)

    if target_name is None:
        return None

    return TaskPlan(
        goal=goal,
        steps=[
            TaskStep(
                id="select_item_in_hotbar",
                kind="use_tool",
                args={
                    "tool": "select_item_in_hotbar",
                    "arguments": {
                        "target_item_name": target_name,
                    },
                },
            )
        ],
    )


def try_parse_select_hotbar_slot(goal: str) -> TaskPlan | None:
    if not wants_select_hotbar_slot(goal):
        return None

    lower = goal.lower()
    match = re.search(r"слот\s*(\d+)", lower)

    if not match:
        return None

    target_slot = int(match.group(1))

    if not (0 <= target_slot <= 8):
        return None

    return TaskPlan(
        goal=goal,
        steps=[
            TaskStep(
                id="select_hotbar_slot",
                kind="use_tool",
                args={
                    "tool": "select_hotbar_slot",
                    "arguments": {
                        "target_slot": target_slot,
                    },
                },
            )
        ],
    )


def parse_task_plan(goal: str) -> TaskPlan:
    """
    Narrow deterministic parser for known goal templates.

    If no template matches, we return an empty plan and let the LLM act
    in the usual free-form mode.
    """
    parsers = [
        try_parse_move_to_coordinates,
        try_parse_select_and_place_block,
        try_parse_place_block_from_hand,
        try_parse_nearby_entity_report,
        try_parse_agent_state_report,
        try_parse_select_hotbar_slot,
        try_parse_select_item_if_present,
        try_parse_select_item_in_hotbar,
        try_parse_remember_move_report,
        try_parse_dig_object,
    ]

    for parser in parsers:
        plan = parser(goal)
        if plan is not None and plan.steps:
            return plan

    return TaskPlan(
        goal=goal,
        steps=[],
    )
