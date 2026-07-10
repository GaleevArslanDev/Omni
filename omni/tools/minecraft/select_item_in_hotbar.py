from omni.clients.minecraft.client import MinecraftClient
from omni.tools.base import Tool


class SelectItemInHotbarTool(Tool):
    name = "select_item_in_hotbar"
    description = (
        "Найти в hotbar предмет по его internal name и выбрать соответствующий слот автоматически. "
        "Это основной инструмент для переключения на предмет, когда известен предмет, а не номер слота. "
        "Если нужен предмет вроде oak_log, sword, pickaxe и т.д., используй именно этот инструмент, "
        "а не select_hotbar_slot."
    )
    args_schema = {
        "target_item_name": "string | null - название предмета, на слот с которым необходимо переключиться. Например, oak_log. Или null, если необходимо выбрать пустой слот"
    }

    def use(self, client: MinecraftClient, arguments: dict):
        target_item_name = arguments.get("target_item_name")

        inventory = client.get_inventory()
        main_hand = inventory["main_hand"]
        hotbar = inventory["hotbar"]

        found = False
        slot = 0
        for item in hotbar:
            if item is None and target_item_name is None:
                found = True
                break
            if item is not None and item["name"] == target_item_name:
                found = True
                break
            slot += 1

        if found:
            success, res = client.select_hotbar_slot(target_slot=slot)
            res["previous_item_name"] = main_hand["name"] if main_hand is not None else None
            new_main_hand = client.get_inventory()["main_hand"]
            res["current_item_name"] = new_main_hand["name"] if new_main_hand is not None else None
            res["intended_item_name"] = target_item_name
        else:
            success, res = False, {"error": "item_not_found", "intended_item_name": target_item_name}
        return success, res
