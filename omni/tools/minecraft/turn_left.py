from omni.clients.minecraft.client import MinecraftClient
from omni.tools.base import Tool


class TurnLeftTool(Tool):
    enabled = False

    name = "turn_left"
    description = "Повернуться влево на deg градусов."
    args_schema = {
        "deg": "float - на сколько градусов надо повернуться"
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, dict]:
        deg = arguments["deg"]

        before = client.observe()["rotation"]
        success = client.turn_by_degrees(-deg)
        after = client.observe()["rotation"]

        return success, {
            "old_rotation": before,
            "new_rotation": after,
            "deg": deg,
        }
