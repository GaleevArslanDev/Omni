from omni.clients.minecraft.client import MinecraftClient
from omni.tools.base import Tool


class ReportAgentStateTool(Tool):
    name = "report_agent_state"
    description = "Детерминированно сообщает состояние агента: здоровье, сытость, координаты, поворот, выбранный слот, предмет в руке, инвентарь, наличие или количество предмета."
    args_schema = {
        "field": "string - one of: health, food, position, rotation, selected_slot, main_hand, inventory_summary, inventory_has_item, inventory_count_item",
        "item_name": "string - optional item name for inventory_has_item or inventory_count_item"
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, dict]:
        observation = client.observe()
        inventory = observation["inventory"]

        field = arguments["field"]
        item_name = arguments.get("item_name")

        if field == "health":
            text = f"Моё здоровье: {observation['health']}"

        elif field == "food":
            text = f"Моя сытость: {observation['food']}"

        elif field == "position":
            pos = observation["position"]
            text = f"Мои координаты: X={pos['x']}, Y={pos['y']}, Z={pos['z']}"

        elif field == "rotation":
            rot = observation["rotation"]
            text = f"Мой поворот: yaw={rot['yaw']}, pitch={rot['pitch']}"

        elif field == "selected_slot":
            selected_slot = inventory["selected_slot"]
            text = f"Мой выбранный слот: {selected_slot}"

        elif field == "main_hand":
            main_hand = inventory["main_hand"]
            if main_hand is None:
                text = "У меня в руке ничего нет."
            else:
                text = (
                    f"У меня в руке {main_hand['display_name']} "
                    f"(name={main_hand['name']}, count={main_hand['count']})."
                )

        elif field == "inventory_summary":
            summary = inventory["summary"]
            if not summary:
                text = "Мой инвентарь пуст."
            else:
                parts = [f"{name}: {count}" for name, count in sorted(summary.items())]
                text = "В моём инвентаре: " + ", ".join(parts)

        elif field == "inventory_has_item":
            if not item_name:
                return False, {"error": "item_name is required for inventory_has_item"}

            count = int(inventory["summary"].get(item_name, 0))
            if count > 0:
                text = f"Да, у меня есть {item_name} в инвентаре."
            else:
                text = f"Нет, у меня нет {item_name} в инвентаре."

        elif field == "inventory_count_item":
            if not item_name:
                return False, {"error": "item_name is required for inventory_count_item"}

            count = int(inventory["summary"].get(item_name, 0))
            text = f"У меня {count} предметов {item_name} в инвентаре."

        else:
            return False, {"error": f"unknown field: {field}"}

        client.say(text)
        return True, {"field": field, "text": text, "item_name": item_name}
