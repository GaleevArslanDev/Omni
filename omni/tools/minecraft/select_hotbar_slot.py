from omni.clients.minecraft.client import MinecraftClient
from omni.tools.base import Tool


class SelectHotbarSlotTool(Tool):
    name = "select_hotbar_slot"
    description = (
        "Выбрать hotbar-слот по его точному номеру от 0 до 8. "
        "Используй этот инструмент только тогда, когда номер слота уже явно задан пользователем, "
        "планом задачи или другим детерминированным шагом. "
        "Не используй его для поиска предмета по наблюдению."
    )
    args_schema = {
        "target_slot": "int - номер слота, который необходимо выбрать, число от 0 до 8"
    }

    def use(self, client: MinecraftClient, arguments: dict):
        target_slot = arguments.get("target_slot")
        return client.select_hotbar_slot(target_slot=target_slot)
