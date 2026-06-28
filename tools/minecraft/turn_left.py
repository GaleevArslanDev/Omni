from clients.minecraft.client import MinecraftClient
from tool import Tool


class TurnLeftTool(Tool):
    name = "turn_left"
    description = "Повернуться влево на deg градусов."
    args_schema = {
        "deg": "int - на сколько градусов надо повернуться"
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, None]:
        deg = arguments["deg"]
        client.turn_by_degrees(-deg)
        return True, None
