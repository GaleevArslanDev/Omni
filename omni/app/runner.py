import logging
from typing import Any

from omni.app.observation_diff import diff_observations
from omni.clients.interface import ClientInterface
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
MAX_STEPS = 20


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

    while step < MAX_STEPS:
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
