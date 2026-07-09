from omni.clients.interface import ClientInterface
from omni.tools.base import Tool


class ObserveTool(Tool):
    enabled = False

    name = "observe"
    description = "Получить текущее наблюдение агента."
    args_schema = {}

    def use(self, client: ClientInterface, arguments) -> tuple[bool, dict]:
        return True, client.observe()
