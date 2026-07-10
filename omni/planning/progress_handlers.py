from typing import TYPE_CHECKING

from omni.planning.task_plan import TaskStep
from omni.state.action import ActionEntry

if TYPE_CHECKING:
    from omni.planning.task_progress import TaskProgress


def update_progress_from_observation(
    task_progress: "TaskProgress",
    observation: dict,
    step_number: int,
) -> None:
    current = task_progress.current_step()

    if current is None:
        return

    if current.kind != "remember_object_location":
        return

    target_name = current.args["target_name"]
    nearby = observation.get("vision", {}).get("nearby_objects", [])

    for obj in nearby:
        if obj.get("name") != target_name:
            continue

        pos = {
            "x": obj["x"],
            "y": obj["y"],
            "z": obj["z"],
        }

        task_progress.remembered_objects[target_name] = pos

        task_progress.mark_done(
            current.id,
            (
                f"nearest {target_name} observed at "
                f"X={pos['x']}, Y={pos['y']}, Z={pos['z']} "
                f"on step {step_number}"
            ),
        )
        return


def update_progress_from_action(task_progress: "TaskProgress", action: ActionEntry) -> None:
    current = task_progress.current_step()

    if current is None:
        return

    if current.kind == "remember_object_location":
        _update_remember_step_from_action(task_progress, current, action)
        return

    if current.kind == "use_tool":
        _update_use_tool_step(task_progress, current, action)
        return

    if current.kind == "select_item_in_hotbar_or_say_missing":
        _update_select_item_or_report_missing_step(task_progress, current, action)
        return

    if current.kind == "report_remembered_location":
        _update_report_step(task_progress, current, action)
        return

    if current.kind == "report_observation_diff":
        _update_report_observation_diff_step(task_progress, current, action)
        return


def _update_remember_step_from_action(
    task_progress: "TaskProgress",
    current: TaskStep,
    action: ActionEntry,
) -> None:
    """
    Если current_step = remember_object_location, а агент сказал,
    что не наблюдает target, считаем задачу терминально невыполнимой.

    Это важно: иначе он будет бесконечно повторять say.
    """
    target_name = current.args["target_name"]

    if action.tool != "say":
        task_progress.mark_failed(
            current.id,
            (
                f"cannot remember {target_name}: invalid tool {action.tool!r} "
                f"used on remember step {action.step}"
            ),
        )
        return

    if not action.success:
        return

    text = action.arguments.get("text", "").lower()

    says_not_observed = (
        "не наблюдаю" in text
        or "не вижу" in text
        or "не найден" in text
        or "нет" in text
    )

    mentions_target = target_name.lower() in text

    if says_not_observed and mentions_target:
        task_progress.mark_failed(
            current.id,
            f"cannot remember {target_name}: agent reported it is not observed on step {action.step}",
        )


def _update_use_tool_step(
    task_progress: "TaskProgress",
    current: TaskStep,
    action: ActionEntry,
) -> None:
    expected_tool = current.args["tool"]
    expected_arguments = current.args.get("arguments", {})

    if action.tool != expected_tool:
        return

    if not action.success:
        task_progress.mark_failed(
            current.id,
            f"{expected_tool} failed on step {action.step}: {action.result}",
        )
        return

    if expected_tool == "move_forward":
        expected_secs = expected_arguments.get("secs")
        actual_secs = action.arguments.get("secs")

        if expected_secs is not None and float(actual_secs) != float(expected_secs):
            return

    if expected_tool == "look_at_nearest":
        expected_name = expected_arguments.get("block_name")
        looked_name = (
            (action.result or {})
            .get("block_at_cursor_after", {})
            .get("name")
        )

        if expected_name is not None and looked_name != expected_name:
            task_progress.mark_failed(
                current.id,
                (
                    f"look_at_nearest pointed at {looked_name!r} instead of "
                    f"{expected_name!r} on step {action.step}"
                ),
            )
            return

    if expected_tool == "dig_block_at_cursor":
        expected_name = expected_arguments.get("expected_name")
        dug_name = (
            (action.result or {})
            .get("dug_block", {})
            .get("name")
        )

        if expected_name is not None and dug_name != expected_name:
            task_progress.mark_failed(
                current.id,
                (
                    f"dig_block_at_cursor dug {dug_name!r} instead of "
                    f"{expected_name!r} on step {action.step}"
                ),
            )
            return

    task_progress.mark_done(
        current.id,
        f"{expected_tool} succeeded with args={action.arguments} on step {action.step}",
    )


def _update_report_step(
    task_progress: "TaskProgress",
    current: TaskStep,
    action: ActionEntry,
) -> None:
    if not action.success:
        task_progress.mark_failed(
            current.id,
            f"report step failed on step {action.step}: {action.result}",
        )
        return

    if action.tool != "say":
        return

    target_name = current.args["target_name"]
    text = action.arguments.get("text", "").lower()

    has_target_name = target_name.lower() in text
    has_coordinates = "x=" in text and "y=" in text and "z=" in text

    if not has_target_name and not has_coordinates:
        return

    task_progress.mark_done(
        current.id,
        f"reported remembered location on step {action.step}: {action.arguments.get('text')}",
    )


def _update_select_item_or_report_missing_step(
    task_progress: "TaskProgress",
    current: TaskStep,
    action: ActionEntry,
) -> None:
    target_name = current.args["target_item_name"]

    if not action.success:
        task_progress.mark_failed(
            current.id,
            f"conditional select step failed on step {action.step}: {action.result}",
        )
        return

    if action.tool == "select_item_in_hotbar":
        selected_name = (action.result or {}).get("current_item_name")
        if selected_name != target_name:
            task_progress.mark_failed(
                current.id,
                (
                    f"conditional select step equipped {selected_name!r} instead of "
                    f"{target_name!r} on step {action.step}"
                ),
            )
            return

        task_progress.mark_done(
            current.id,
            f"equipped {target_name} from hotbar on step {action.step}",
        )
        return

    if action.tool == "say":
        text = action.arguments.get("text", "").lower()
        if target_name.lower() in text:
            task_progress.mark_done(
                current.id,
                f"reported missing {target_name} on step {action.step}",
            )
        return


def _update_report_observation_diff_step(
    task_progress: "TaskProgress",
    current: TaskStep,
    action: ActionEntry,
) -> None:
    if not action.success:
        task_progress.mark_failed(
            current.id,
            f"report observation diff failed on step {action.step}: {action.result}",
        )
        return

    if action.tool != "say":
        return

    target_name = current.args["target_name"]
    text = action.arguments.get("text", "").lower()

    current_index = next(
        (index for index, step in enumerate(task_progress.plan.steps) if step.id == current.id),
        None,
    )

    if current_index is None:
        task_progress.mark_failed(
            current.id,
            f"report_observation_diff step {current.id} is missing from TaskPlan",
        )
        return

    last_dig_step = None
    for step in reversed(task_progress.plan.steps[:current_index]):
        if step.kind == "use_tool" and step.args.get("tool") == "dig_block_at_cursor":
            last_dig_step = step
            break

    if last_dig_step is None:
        task_progress.mark_failed(
            current.id,
            f"report_observation_diff has no preceding dig step for {target_name}",
        )
        return

    has_target_name = target_name.lower() in text
    mentions_disappearance = (
        "исчез" in text
        or "пропал" in text
        or "removed" in text
        or "сломан" in text
        or "больше нет" in text
    )
    mentions_cursor_change = "block_at_cursor" in text

    if not has_target_name:
        return

    if not mentions_disappearance and not mentions_cursor_change:
        return

    task_progress.mark_done(
        current.id,
        f"reported observation diff on step {action.step}: {action.arguments.get('text')}",
    )
