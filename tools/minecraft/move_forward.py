from clients.minecraft.client import MinecraftClient
from tool import Tool


class MoveForwardTool(Tool):
    name = "move_forward"
    description = "Двигаться вперед secs секунд."
    args_schema = {
        "secs": "int - длительность движения в секундах"
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, None]:
        secs = arguments["secs"]
        client.set_control_state_for("forward", secs)
        return True, None
