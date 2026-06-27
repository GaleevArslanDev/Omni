import json

from client_interface import ClientInterface
from llm import call_llm
from minecraft_client import MinecraftClient
from prompt import create_prompt
from tool_registry import ToolRegistry
from tools.common.done import DoneTool
from tools.minecraft import (
    MoveForwardTool,
    ObserveTool,
    SayTool,
    TurnLeftTool,
    TurnRightTool,
)


registry = ToolRegistry([
    DoneTool(),
    SayTool(),
    MoveForwardTool(),
    TurnRightTool(),
    TurnLeftTool(),
])


def call_llm_json(prompt: str) -> dict:
    can_exit = False
    while not can_exit:
        raw_answer = call_llm(prompt)
        try:
            answer = json.loads(raw_answer)
            can_exit = True
        except Exception as e:
            print("Error just happened, trying to repeat the request to LLM:", e)

    return answer


def make_history_entry(answer: dict, success: bool, res: str | int | float | None) -> str:
    h = (
        f"ACTION_DONE: {answer['tool_use']['name']} "
        f"ARGS: {json.dumps(answer['tool_use']['arguments'], ensure_ascii=False)} "
        f"SUCCESS: {success} "
        f"RESULT: {res}"
        f"MESSAGE: {answer["history"]}"
    )
    return h


def run_agent_loop(client: ClientInterface, goal: str) -> None:
    history = ["Сейчас еще нет плана."]

    last_tool = None

    while True:
        observations = client.observe()
        prompt = create_prompt(
            goal=goal,
            observations=observations,
            history=history,
            tools_description=registry.describe()
        )

        answer = call_llm_json(prompt)
        tools_use = answer["tool_use"]

        if tools_use["name"] == "done":
            print(answer["user_answer"])
            if callable(getattr(client, "stop", None)):
                client.stop()
            break

        tool_key = json.dumps(tools_use, ensure_ascii=False, sort_keys=True)

        print(answer)
        print(answer["user_answer"])

        if tool_key == last_tool:
            history.append(
                "SYSTEM: Ты только что повторил то же самое действие. "
                "Если цель уже выполнена, используй done."
            )
            print("Повтор действия")
            continue

        last_tool = tool_key

        success, res = registry.use(client, tools_use)
        history.append(make_history_entry(answer, success, res))



if __name__ == "__main__":
    client = MinecraftClient()
    goal = input("> ")
    run_agent_loop(client, goal)