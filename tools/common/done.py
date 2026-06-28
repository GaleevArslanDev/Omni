from client_interface import ClientInterface
from tool import Tool


class DoneTool(Tool):
    name = "done"
    description = "Завершить работу. Используй, когда цель уже достигнута."
    args_schema = {}

    def use(self, client: ClientInterface, arguments: dict) -> tuple[bool, None]:
        return True, None
