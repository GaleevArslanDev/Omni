import logging
from typing import Any

from omni.app.observation_diff import diff_observations
from omni.clients.interface import ClientInterface
from omni.config import AGENT_MAX_STEPS
from omni.llm.json_client import safe_call_llm_json
from omni.planning.parsers import parse_task_plan
from omni.planning.task_plan import TaskPlan
from omni.planning.task_progress import TaskProgress
from omni.prompt.builder import create_prompt
from omni.state.action import ActionEntry
from omni.state.agent_state import AgentState
from omni.state.memory import MemoryEntry
from omni.state.world_state import WorldState
from omni.tools.loader import load_tools
from omni.tools.registry import ToolRegistry

registry = ToolRegistry(load_tools())
logger = logging.getLogger(__name__)


def _create_run_state(goal: str) -> tuple[
    list[ActionEntry],
    list[MemoryEntry],
    WorldState,
    AgentState,
    TaskPlan,
    TaskProgress,
    bool,
]:
    action_log: list[ActionEntry] = []
    memory_log: list[MemoryEntry] = []

    world_state = WorldState()
    agent_state = AgentState()

    task_plan = parse_task_plan(goal)
    task_progress = TaskProgress(task_plan)
    planned_mode = len(task_plan.steps) > 0

    return (
        action_log,
        memory_log,
        world_state,
        agent_state,
        task_plan,
        task_progress,
        planned_mode,
    )


def _observe_and_update_state(
    client: ClientInterface,
    world_state: WorldState,
    agent_state: AgentState,
    task_progress: TaskProgress,
    step: int,
) -> dict[str, Any]:
    observations = client.observe()

    world_state.update_from_observation(observations, step)
    agent_state.update_from_observation(observations, step)
    task_progress.update_from_observation(observations, step)

    return observations


def _log_step_context(
    observations: dict[str, Any],
    task_plan: TaskPlan,
    task_progress: TaskProgress,
) -> None:
    logger.info("Observations: %s", observations)
    logger.info("TASK_PLAN: %s", task_plan.to_json())
    logger.info("TASK_PROGRESS: %s", task_progress.to_json())


def _should_stop_for_terminal_progress(
    client: ClientInterface,
    planned_mode: bool,
    task_progress: TaskProgress,
) -> bool:
    if not planned_mode or not task_progress.is_terminal():
        return False

    logger.info("[TASK_TERMINAL]%s", task_progress.to_json())
    client.stop()
    return True


def _build_prompt(
    goal: str,
    observations: dict[str, Any],
    action_log: list[ActionEntry],
    memory_log: list[MemoryEntry],
    world_state: WorldState,
    agent_state: AgentState,
    task_plan: TaskPlan,
    task_progress: TaskProgress,
) -> str:
    return create_prompt(
        goal=goal,
        observations=observations,
        actions=action_log,
        memory=memory_log,
        world_state=world_state,
        agent_state=agent_state,
        task_plan=task_plan,
        task_progress=task_progress,
        tools_description=registry.describe(),
    )


def _request_next_action(prompt: str) -> tuple[dict[str, Any], dict[str, Any]]:
    answer = safe_call_llm_json(prompt)
    tools_use = answer["tool_use"]

    logger.info("LLM answer: %s", answer)
    logger.info("LLM user answer: %s", answer["user_answer"])

    return answer, tools_use


def _build_report_remembered_location_text(task_progress: TaskProgress) -> str | None:
    current_step = task_progress.current_step()
    if current_step is None or current_step.kind != "report_remembered_location":
        return None

    target_name = current_step.args["target_name"]
    remembered = task_progress.remembered_objects.get(target_name)
    if remembered is None:
        return f"Позиция объекта {target_name} не была запомнена."

    return (
        f"Запомненный {target_name} был по координатам "
        f"X={remembered['x']}, Y={remembered['y']}, Z={remembered['z']}."
    )


def _build_report_observation_diff_text(
    task_progress: TaskProgress,
    action_log: list[ActionEntry],
) -> str | None:
    current_step = task_progress.current_step()
    if current_step is None or current_step.kind != "report_observation_diff":
        return None

    if not action_log:
        return None

    target_name = current_step.args["target_name"]
    observation_diff = action_log[-1].observation_diff or {}

    disappeared = observation_diff.get("nearby_objects_disappeared", [])
    target_disappeared = any(obj.get("name") == target_name for obj in disappeared)

    parts: list[str] = []
    if target_disappeared:
        parts.append(f"{target_name} исчез из nearby_objects")

    cursor_after = observation_diff.get("block_at_cursor_after") or {}
    cursor_name = cursor_after.get("name")
    if cursor_name is not None:
        parts.append(f"block_at_cursor теперь {cursor_name}")

    if not parts:
        return f"Я не наблюдаю подтвержденных изменений для {target_name}."

    return ". ".join(parts) + "."


def _build_select_item_or_report_missing_answer(
    current_step,
    observations: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    if current_step.kind != "select_item_in_hotbar_or_say_missing":
        return None

    target_name = current_step.args["target_item_name"]
    hotbar = observations.get("inventory", {}).get("hotbar", [])
    has_item = any(item is not None and item.get("name") == target_name for item in hotbar)

    if has_item:
        answer = {
            "user_answer": f"Беру {target_name} в руку из hotbar.",
            "tool_use": {
                "name": "select_item_in_hotbar",
                "arguments": {"target_item_name": target_name},
            },
            "history": f"Deterministically selected {target_name} from hotbar.",
        }
        return answer, answer["tool_use"]

    text = f"У меня нет {target_name} в hotbar."
    answer = {
        "user_answer": text,
        "tool_use": {
            "name": "say",
            "arguments": {"text": text},
        },
        "history": text,
    }
    return answer, answer["tool_use"]


def _planned_step_answer(
    task_progress: TaskProgress,
    action_log: list[ActionEntry],
    observations: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    current_step = task_progress.current_step()
    if current_step is None:
        return None

    if current_step.kind == "use_tool":
        tool_name = current_step.args["tool"]
        arguments = current_step.args["arguments"]

        answer = {
            "user_answer": f"Детерминированно выполняю шаг {tool_name}.",
            "tool_use": {
                "name": tool_name,
                "arguments": arguments,
            },
            "history": f"Deterministically executed planned tool {tool_name} with args={arguments}.",
        }
        return answer, answer["tool_use"]

    if current_step.kind == "report_remembered_location":
        text = _build_report_remembered_location_text(task_progress)
        if text is None:
            return None

        answer = {
            "user_answer": text,
            "tool_use": {
                "name": "say",
                "arguments": {"text": text},
            },
            "history": text,
        }
        return answer, answer["tool_use"]

    if current_step.kind == "report_observation_diff":
        text = _build_report_observation_diff_text(task_progress, action_log)
        if text is None:
            return None

        answer = {
            "user_answer": text,
            "tool_use": {
                "name": "say",
                "arguments": {"text": text},
            },
            "history": text,
        }
        return answer, answer["tool_use"]

    if current_step.kind == "select_item_in_hotbar_or_say_missing":
        return _build_select_item_or_report_missing_answer(current_step, observations)

    return None


def _handle_done_tool(client: ClientInterface) -> None:
    logger.info("[TASK_TERMINAL] LLM finished execution with done tool")
    client.stop()


def _record_action_and_memory(
    step: int,
    observations_before: dict[str, Any],
    client: ClientInterface,
    tools_use: dict[str, Any],
    answer: dict[str, Any],
    action_log: list[ActionEntry],
    memory_log: list[MemoryEntry],
    world_state: WorldState,
    task_progress: TaskProgress,
) -> None:
    success, result = registry.use(client, tools_use)

    observations_after = client.observe()
    observation_diff = diff_observations(observations_before, observations_after)

    action = ActionEntry(
        step=step,
        tool=tools_use["name"],
        arguments=tools_use["arguments"],
        success=success,
        result=result,
        observation_diff=observation_diff,
    )
    action_log.append(action)

    world_state.update_from_action(action)
    task_progress.update_from_action(action)

    memory_log.append(
        MemoryEntry(
            step=step,
            text=answer["history"],
        )
    )


def run_agent_loop(client: ClientInterface, goal: str) -> None:
    (
        action_log,
        memory_log,
        world_state,
        agent_state,
        task_plan,
        task_progress,
        planned_mode,
    ) = _create_run_state(goal)

    logger.info("Started with planned mode: %s", planned_mode)

    step = 0
    terminated_normally = False

    while step < AGENT_MAX_STEPS:
        step += 1

        observations = _observe_and_update_state(
            client,
            world_state,
            agent_state,
            task_progress,
            step,
        )
        _log_step_context(observations, task_plan, task_progress)

        if _should_stop_for_terminal_progress(client, planned_mode, task_progress):
            terminated_normally = True
            break

        planned_execution = _planned_step_answer(task_progress, action_log, observations)
        if planned_execution is not None:
            answer, tools_use = planned_execution
            logger.info("Deterministic planned execution: %s", answer)
        else:
            prompt = _build_prompt(
                goal,
                observations,
                action_log,
                memory_log,
                world_state,
                agent_state,
                task_plan,
                task_progress,
            )
            answer, tools_use = _request_next_action(prompt)

        if tools_use["name"] == "done":
            _handle_done_tool(client)
            terminated_normally = True
            break

        _record_action_and_memory(
            step,
            observations,
            client,
            tools_use,
            answer,
            action_log,
            memory_log,
            world_state,
            task_progress,
        )

    if not terminated_normally:
        logger.warning("Terminated because of the timeout")
        client.stop()
