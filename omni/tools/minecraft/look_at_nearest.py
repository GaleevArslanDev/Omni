from typing import Any

from omni.clients.minecraft.client import MinecraftClient
from omni.tools.base import Tool


class LookAtNearestTool(Tool):
    name = "look_at_nearest"
    description = "Посмотреть на ближайший блок нужного типа."
    args_schema = {
        "block_name": "str - тип блока. Например, oak_log",
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, dict[str, Any]]:
        target_name = arguments["block_name"]
        blocks = client.observe()["vision"]["nearby_objects"]
        nearest_block = next((b for b in blocks if b["name"] == target_name), None)

        if not nearest_block:
            return False, {"error": "no_such_block_in_nearest_objects"}

        x, y, z = nearest_block["x"] + 0.5, nearest_block["y"] + 0.5, nearest_block["z"] + 0.5

        before = client.observe()["vision"]["block_at_cursor"]
        success = client.look_at_coords(x, y, z)
        after = client.observe()["vision"]["block_at_cursor"]

        return success, {
            "looked_at": {"x": x, "y": y, "z": z},
            "block_at_cursor_before": before,
            "block_at_cursor_after": after,
        }