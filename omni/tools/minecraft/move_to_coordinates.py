from omni.clients.minecraft.client import MinecraftClient
from omni.tools.base import Tool


class MoveToCoordinates(Tool):
    name = "move_to_coordinates"
    description = "Дойти до координат."
    args_schema = {
        "x": "float - координата X",
        "y": "float - координата Y",
        "z": "float - координата Z",
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, dict]:
        x, y, z = arguments["x"], arguments["y"], arguments["z"]
        before = client.observe()["position"]
        success, move_result = client.move_to_coordinates(x, y, z)
        after = client.observe()["position"]

        return success, {
            "old_position": before,
            "new_position": after,
            "target_position": {"x": x, "y": y, "z": z},
            **move_result,
        }
