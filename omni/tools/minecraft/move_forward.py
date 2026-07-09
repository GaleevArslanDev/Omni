from omni.clients.minecraft.client import MinecraftClient
from omni.tools.base import Tool


class MoveForwardTool(Tool):
    name = "move_forward"
    description = "Двигаться вперед secs секунд."
    args_schema = {
        "secs": "float - длительность движения в секундах"
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, dict]:
        secs = arguments["secs"]

        before = client.observe()["position"]
        client.set_control_state_for("forward", secs)
        after = client.observe()["position"]

        return True, {
            "old_position": before,
            "new_position": after,
            "secs": secs,
        }
