from clients.minecraft.client import MinecraftClient
from tool import Tool


class DigBlockAtCursor(Tool):
    name = "dig_block_at_cursor"
    description = "Добыть блок, расположенный в направлении взгляда. Можно указать expected_name, чтобы не сломать не тот блок."
    args_schema = {
        "expected_name": "string | null - ожидаемое имя блока, например oak_log"
    }

    def use(self, client: MinecraftClient, arguments: dict):
        expected_name = arguments.get("expected_name")
        return client.dig_block_at_cursor(expected_name=expected_name)