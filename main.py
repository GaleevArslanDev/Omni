import json

import logger
from action import ActionEntry
from agent_state import AgentState
from client_interface import ClientInterface
from llm import call_llm
from clients.minecraft.client import MinecraftClient
from memory import MemoryEntry
from prompt import create_prompt
from task_plan import parse_task_plan
from task_progress import TaskProgress
from tool_registry import ToolRegistry
from tools_loader import load_tools
from world_state import WorldState

registry = ToolRegistry(load_tools())


def safe_call_llm_json(prompt: str) -> dict:
    for _ in range(5):
        raw_answer = call_llm(prompt)
        try:
            answer = json.loads(raw_answer)
            return answer
        except Exception as e:
            logger.log_error(e)
            logger.log_message("Trying again...")

    logger.log_error(ValueError("Tried to call LLM JSON 5 times but failed"))
    raise ValueError("Tried to call LLM JSON 5 times but failed")


def object_key(obj: dict) -> tuple:
    return (
        obj["name"],
        obj["x"],
        obj["y"],
        obj["z"],
    )


def diff_observations(before: dict, after: dict) -> dict:
    before_objects = before["vision"]["nearby_objects"]
    after_objects = after["vision"]["nearby_objects"]

    before_set = {object_key(obj): obj for obj in before_objects}
    after_set = {object_key(obj): obj for obj in after_objects}

    disappeared = [
        before_set[key]
        for key in before_set.keys() - after_set.keys()
    ]

    appeared = [
        after_set[key]
        for key in after_set.keys() - before_set.keys()
    ]

    return {
        "nearby_objects_disappeared": disappeared,
        "nearby_objects_appeared": appeared,
        "block_at_cursor_before": before["vision"]["block_at_cursor"],
        "block_at_cursor_after": after["vision"]["block_at_cursor"],
    }


def run_agent_loop(client: ClientInterface, goal: str) -> None:
    action_log = []
    memory_log = []

    world_state = WorldState()
    agent_state = AgentState()

    task_plan = parse_task_plan(goal)
    task_progress = TaskProgress(task_plan)

    planned_mode = len(task_plan.steps) > 0

    max_steps = 20

    print("Started with planned mode:", planned_mode)

    #last_tool = None

    step = 0

    terminated_normally = False

    while step < max_steps:
        step += 1

        observations = client.observe()

        world_state.update_from_observation(observations, step)
        agent_state.update_from_observation(observations, step)
        task_progress.update_from_observation(observations, step)

        print(observations)
        print("TASK_PLAN:", task_plan.to_json())
        print("TASK_PROGRESS:", task_progress.to_json())

        if planned_mode and task_progress.is_terminal():
            logger.log_message("[TASK_TERMINAL]" + str(task_progress.to_json()))
            if callable(getattr(client, "stop", None)):
                client.stop()
            terminated_normally = True
            break

        prompt = create_prompt(
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

        answer = safe_call_llm_json(prompt)
        tools_use = answer["tool_use"]

        if tools_use["name"] == "done":
            logger.log_message("[TASK_TERMINAL] LLM finished execution with done tool")
            if callable(getattr(client, "stop", None)):
                client.stop()
                terminated_normally = True
            break

        # tool_key = json.dumps(tools_use, ensure_ascii=False, sort_keys=True)

        print(answer)
        print(answer["user_answer"])

        # if tool_key == last_tool:
        #     history.append(
        #         "SYSTEM: Ты только что повторил то же самое действие. "
        #         "Если цель уже выполнена, используй done."
        #     )
        #     print("Повтор действия")
        #     continue
        #
        # last_tool = tool_key

        success, res = registry.use(client, tools_use)

        obs_after = client.observe()
        diff = diff_observations(observations, obs_after)

        action = ActionEntry(
            step=step,
            tool=tools_use["name"],
            arguments=tools_use["arguments"],
            success=success,
            result=res,
            observation_diff=diff,
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

    if not terminated_normally:
        # Timeout
        logger.log_warning("Terminated because of the timeout")
        if callable(getattr(client, "stop", None)):
            client.stop()


if __name__ == "__main__":
    client = MinecraftClient()
    goal = input("> ")
    run_agent_loop(client, goal)
