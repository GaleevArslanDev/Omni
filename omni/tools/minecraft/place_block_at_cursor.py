from omni.clients.minecraft.client import MinecraftClient
from omni.tools.base import Tool


class PlaceBlockAtCursorTool(Tool):
    name = "place_block_at_cursor"
    description = (
        "Поставить блок из основной руки на грань блока, находящегося под курсором. "
        "По умолчанию ставит сверху на блок под курсором."
    )
    args_schema = {
        "face": "string - optional face: top, bottom, north, south, west, east. Default: top",
        "expected_item_name": "string | null - optional expected item name in main hand, for example oak_log",
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, dict]:
        face = arguments.get("face", "top")
        expected_item_name = arguments.get("expected_item_name")
        return client.place_block_at_cursor(
            face=face,
            expected_item_name=expected_item_name,
        )
