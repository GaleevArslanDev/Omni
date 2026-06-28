from typing import Any

import logger
from client_interface import ClientInterface
from tool import Tool


class ToolRegistry:
    def __init__(self, tools: list[Tool]):
        self.tools = {tool.name: tool for tool in tools}

    def use(self, client: ClientInterface, tool_data: dict) ->tuple[bool, Any | None]:
        name = tool_data["name"]
        arguments = tool_data.get("arguments", {})

        tool = self.tools.get(name)
        if tool is None:
            return False, f"Unknown tool: {name}"

        try:
            return tool.use(client, arguments)
        except Exception as e:
            logger.log_error(e)
            return False, f"Tool error: {e}"

    def describe(self) -> str:
        lines = []
        for tool in self.tools.values():
            lines.append(
                f'{tool.name}({tool.args_schema}) - {tool.description}'
            )
        return "\n".join(lines)
