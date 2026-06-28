import json

import logger
from action import ActionEntry
from client_interface import ClientInterface
from llm import call_llm
from clients.minecraft.client import MinecraftClient
from memory import MemoryEntry
from prompt import create_prompt
from tool_registry import ToolRegistry
from tools_loader import load_tools

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


def run_agent_loop(client: ClientInterface, goal: str) -> None:
    action_log = []
    memory_log = []

    #last_tool = None

    step = 0

    while True:
        step += 1
        observations = client.observe()
        print(observations)
        prompt = create_prompt(
            goal=goal,
            observations=observations,
            actions=action_log,
            memory=memory_log,
            tools_description=registry.describe(),
        )

        answer = safe_call_llm_json(prompt)
        tools_use = answer["tool_use"]

        if tools_use["name"] == "done":
            print(answer["user_answer"])
            if callable(getattr(client, "stop", None)):
                client.stop()
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
        action_log.append(
            ActionEntry(
                step=step,
                tool=tools_use["name"],
                arguments=tools_use["arguments"],
                success=success,
                result=res,
            )
        )

        memory_log.append(
            MemoryEntry(
                step=step,
                text=answer["history"],
            )
        )


if __name__ == "__main__":
    client = MinecraftClient()
    goal = input("> ")
    run_agent_loop(client, goal)
