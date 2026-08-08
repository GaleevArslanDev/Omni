from omni.clients.minecraft.client import MinecraftClient
from omni.helpers.entity_targeting import (
    distance_between_positions,
    find_entity_by_id,
    select_nearest_entity_from_observation,
)
from omni.tools.base import Tool


class MoveToNearestEntityTool(Tool):
    name = "move_to_nearest_entity"
    description = (
        "Deterministically selects the nearest observed entity and moves to its current position. "
        "It uses observation['entities'] for targeting and move_to_coordinates for movement. "
        "It does not attack, interact, or persist the entity in WorldState."
    )
    args_schema = {
        "category": "string - one of: nearby, dropped_items, vehicles",
        "target_name": "string - optional entity/item/vehicle name to approach",
        "attitude": "string - optional, one of: hostile, neutral, friendly, utility; only for category=nearby",
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, dict]:
        category = arguments.get("category", "nearby")
        target_name = arguments.get("target_name")
        attitude = arguments.get("attitude")

        before = client.observe()
        success, target_result = select_nearest_entity_from_observation(
            observation=before,
            category=category,
            target_name=target_name,
            attitude=attitude,
        )

        if not success:
            return False, target_result

        target = target_result["target"]
        target_position = target["position"]
        start_position = before["position"]
        start_distance = target.get("distance")

        move_success, move_result = client.move_to_coordinates(
            target_position["x"],
            target_position["y"],
            target_position["z"],
        )

        after = client.observe()
        end_position = after["position"]
        observed_after = find_entity_by_id(
            observation=after,
            category=category,
            entity_id=target.get("id"),
        )
        end_distance = (
            observed_after.get("distance")
            if observed_after is not None
            else distance_between_positions(end_position, target_position)
        )

        result = {
            **target_result,
            "start_position": start_position,
            "end_position": end_position,
            "target_position": target_position,
            "start_distance": start_distance,
            "end_distance": end_distance,
            "target_observed_after": observed_after,
            **move_result,
        }

        if not move_success:
            return False, result

        return True, result
