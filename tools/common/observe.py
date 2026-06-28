from client_interface import ClientInterface
from tool import Tool


class ObserveTool(Tool):
    enabled = False

    name = "observe"
    description = "Получить текущее наблюдение агента."
    args_schema = {}

    def use(self, client: ClientInterface, arguments) -> tuple[bool, dict]:
        return True, client.observe()
