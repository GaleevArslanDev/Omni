from clients.minecraft.client import MinecraftClient
from tool import Tool


class LookAtCoordinatesTool(Tool):
    name = "look_at_coordinates"
    description = "Посмотреть на координаты."
    args_schema = {
        "x": "float - координата x",
        "y": "float - координата y",
        "z": "float - координата z"
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, dict]:
        x, y, z = arguments["x"], arguments["y"], arguments["z"]

        before = client.observe()["vision"]["block_at_cursor"]
        success = client.look_at_coords(x, y, z)
        after = client.observe()["vision"]["block_at_cursor"]

        return success, {
            "looked_at": {"x": x, "y": y, "z": z},
            "block_at_cursor_before": before,
            "block_at_cursor_after": after,
        }
