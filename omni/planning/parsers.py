from omni.planning.goal_rules import (
    extract_seconds,
    resolve_object_name,
    wants_change_report,
    wants_dig,
    wants_move_forward,
    wants_remember,
    wants_report,
)
from omni.planning.task_plan import TaskPlan, TaskStep


def try_parse_remember_move_report(goal: str) -> TaskPlan | None:
    target_name = resolve_object_name(goal)

    if target_name is None:
        return None

    if not wants_remember(goal):
        return None

    steps: list[TaskStep] = []

    steps.append(
        TaskStep(
            id="remember_target_location",
            kind="remember_object_location",
            args={
                "target_name": target_name,
            },
        )
    )

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
        "Р·РґРѕСЂРѕРІ" in lower
        or "health" in lower
        or "hp" in lower
        or "СЃС‹С‚РѕСЃС‚" in lower
        or "food" in lower
        or "РіРѕР»РѕРґ" in lower
        or "РєРѕРѕСЂРґРёРЅР°С‚" in lower
        or "РїРѕР·РёС†Рё" in lower
        or "РіРґРµ С‚С‹" in lower
        or "РїРѕРІРѕСЂРѕС‚" in lower
        or "yaw" in lower
        or "pitch" in lower
        or ("РІС‹Р±СЂР°РЅ" in lower and "СЃР»РѕС‚" in lower)
        or "РІ СЂСѓРєРµ" in lower
        or "РёРЅРІРµРЅС‚Р°СЂ" in lower
        or "Сѓ С‚РµР±СЏ РµСЃС‚СЊ" in lower
        or "РµСЃС‚СЊ Р»Рё Сѓ С‚РµР±СЏ" in lower
        or "СЃРєРѕР»СЊРєРѕ Сѓ С‚РµР±СЏ" in lower
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

    if "Р·РґРѕСЂРѕРІ" in lower or "health" in lower or "hp" in lower:
        return make_plan("report_health", "health")

    if "СЃС‹С‚РѕСЃС‚" in lower or "food" in lower or "РіРѕР»РѕРґ" in lower:
        return make_plan("report_food", "food")

    if "РіРґРµ С‚С‹" in lower or "РєРѕРѕСЂРґРёРЅР°С‚" in lower or "РїРѕР·РёС†Рё" in lower:
        return make_plan("report_position", "position")

    if "РїРѕРІРѕСЂРѕС‚" in lower or "yaw" in lower or "pitch" in lower:
        return make_plan("report_rotation", "rotation")

    if "РІ СЂСѓРєРµ" in lower:
        return make_plan("report_main_hand", "main_hand")

    if "РІС‹Р±СЂР°РЅ" in lower and "СЃР»РѕС‚" in lower:
        return make_plan("report_selected_slot", "selected_slot")

    if "С‡С‚Рѕ Сѓ С‚РµР±СЏ РІ РёРЅРІРµРЅС‚Р°СЂРµ" in lower or "С‡С‚Рѕ РІ РёРЅРІРµРЅС‚Р°СЂРµ" in lower:
        return make_plan("report_inventory_summary", "inventory_summary")

    item_name = resolve_object_name(goal)

    if item_name is not None:
        if "СЃРєРѕР»СЊРєРѕ Сѓ С‚РµР±СЏ" in lower or ("СЃРєРѕР»СЊРєРѕ" in lower and "РІ РёРЅРІРµРЅС‚Р°СЂРµ" in lower):
            return make_plan("report_inventory_count_item", "inventory_count_item", item_name)

        if "Сѓ С‚РµР±СЏ РµСЃС‚СЊ" in lower or "РµСЃС‚СЊ Р»Рё Сѓ С‚РµР±СЏ" in lower:
            return make_plan("report_inventory_has_item", "inventory_has_item", item_name)

    return None


def parse_task_plan(goal: str) -> TaskPlan:
    """
    v0.7 parser.

    Р­С‚Рѕ РќР• СѓРЅРёРІРµСЂСЃР°Р»СЊРЅС‹Р№ РїР»Р°РЅРЅРµСЂ.
    Р­С‚Рѕ РЅР°Р±РѕСЂ РјР°Р»РµРЅСЊРєРёС… РґРµС‚РµСЂРјРёРЅРёСЂРѕРІР°РЅРЅС‹С… СЂР°СЃРїРѕР·РЅР°РІР°С‚РµР»РµР№ РёР·РІРµСЃС‚РЅС‹С… С€Р°Р±Р»РѕРЅРѕРІ.

    РЎРµР№С‡Р°СЃ РїРѕРґРґРµСЂР¶РёРІР°СЋС‚СЃСЏ:

    1. remember/move/report:
       "Р—Р°РїРѕРјРЅРё chest, РїСЂРѕР№РґРё РІРїРµСЂС‘Рґ 3 СЃРµРєСѓРЅРґС‹, СЃРєР°Р¶Рё РіРґРµ Р±С‹Р» chest"

    2. dig/report-diff:
       "РџРѕРІРµСЂРЅРёСЃСЊ Рє oak_log, СЃР»РѕРјР°Р№ РµРіРѕ, СЃРєР°Р¶Рё С‡С‚Рѕ РёР·РјРµРЅРёР»РѕСЃСЊ"

    РЎРјРµС€Р°РЅРЅС‹Рµ РєРѕРјР°РЅРґС‹ СЃ РЅРµСЃРєРѕР»СЊРєРёРјРё СЂР°Р·РЅС‹РјРё С†РµР»СЏРјРё РїРѕРєР° Р»СѓС‡С€Рµ РЅРµ РїРѕРґРґРµСЂР¶РёРІР°С‚СЊ.
    Р•СЃР»Рё РїР°С‚С‚РµСЂРЅ РЅРµ СЂР°СЃРїРѕР·РЅР°РЅ, РІРѕР·РІСЂР°С‰Р°РµРј РїСѓСЃС‚РѕР№ РїР»Р°РЅ.
    РўРѕРіРґР° LLM СЂР°Р±РѕС‚Р°РµС‚ РєР°Рє СЂР°РЅСЊС€Рµ.
    """
    parsers = [
        try_parse_agent_state_report,
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
