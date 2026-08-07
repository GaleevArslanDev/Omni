from omni.clients.minecraft.client import MinecraftClient
from omni.helpers.entity_targeting import select_nearest_entity_from_observation
from omni.tools.base import Tool


class TargetNearestEntityTool(Tool):
    name = "target_nearest_entity"
    description = (
        "Deterministically selects the nearest observed entity from observation['entities']. "
        "It returns the selected entity id, name, kind, position, and distance. "
        "It does not move, attack, interact, or persist the entity in WorldState."
    )
    args_schema = {
        "category": "string - one of: nearby, dropped_items, vehicles",
        "target_name": "string - optional entity/item/vehicle name to target",
        "attitude": "string - optional, one of: hostile, neutral, friendly, utility; only for category=nearby",
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, dict]:
        category = arguments.get("category", "nearby")
        target_name = arguments.get("target_name")
        attitude = arguments.get("attitude")

        observation = client.observe()
        success, result = select_nearest_entity_from_observation(
            observation=observation,
            category=category,
            target_name=target_name,
            attitude=attitude,
        )

        if not success:
            return False, result

        target = result["target"]
        position = target["position"]
        text = (
            f"Selected nearest {target['name']} "
            f"at X={position['x']}, Y={position['y']}, Z={position['z']} "
            f"distance={target['distance']}."
        )
        client.say(text)

        return True, {
            **result,
            "text": text,
        }
