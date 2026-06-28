from minecraft_client import MinecraftClient
from tool import Tool

class LookAtCoordinatesTool(Tool):
    name = "look_at_coordinates"
    description = "Посмотреть на координаты."
    args_schema = {
        "x": "float - координата x",
        "y": "float - координата y",
        "z": "float - координата z"
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, None]:
        x, y, z = arguments["x"], arguments["y"], arguments["z"]
        res = client.look_at_coords(x, y, z)
        return res, None