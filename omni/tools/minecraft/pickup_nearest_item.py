import time

from omni.clients.minecraft.client import MinecraftClient
from omni.config import (
    PICKUP_CONFIRMATION_POLL_INTERVAL_SECONDS,
    PICKUP_CONFIRMATION_TIMEOUT_SECONDS,
)
from omni.helpers.entity_targeting import (
    distance_between_positions,
    find_entity_by_id,
    select_nearest_entity_from_observation,
)
from omni.tools.base import Tool


def _inventory_count(observation: dict, item_name: str) -> int:
    return int(observation.get("inventory", {}).get("summary", {}).get(item_name, 0))


class PickupNearestItemTool(Tool):
    name = "pickup_nearest_item"
    description = (
        "Deterministically picks up the nearest observed dropped item. "
        "It moves to the dropped item position and confirms pickup by checking inventory before and after."
    )
    args_schema = {
        "target_name": "string - optional dropped item name to pick up, for example oak_log",
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, dict]:
        target_name = arguments.get("target_name")

        before = client.observe()
        success, target_result = select_nearest_entity_from_observation(
            observation=before,
            category="dropped_items",
            target_name=target_name,
        )

        if not success:
            return False, target_result

        target = target_result["target"]
        item_name = target["name"]
        target_position = target["position"]
        before_count = _inventory_count(before, item_name)

        move_success, move_result = client.move_to_coordinates(
            target_position["x"],
            target_position["y"],
            target_position["z"],
        )

        after_move = client.observe()
        if not move_success:
            return False, {
                **target_result,
                "error": "approach_failed_before_pickup",
                "item_name": item_name,
                "inventory_count_before": before_count,
                "inventory_count_after": _inventory_count(after_move, item_name),
                "start_position": before["position"],
                "end_position": after_move["position"],
                "move_result": move_result,
            }

        deadline = time.monotonic() + PICKUP_CONFIRMATION_TIMEOUT_SECONDS
        final_observation = after_move
        after_count = _inventory_count(final_observation, item_name)

        while after_count <= before_count and time.monotonic() < deadline:
            time.sleep(PICKUP_CONFIRMATION_POLL_INTERVAL_SECONDS)
            final_observation = client.observe()
            after_count = _inventory_count(final_observation, item_name)

        observed_after = find_entity_by_id(
            observation=final_observation,
            category="dropped_items",
            entity_id=target.get("id"),
        )
        end_position = final_observation["position"]
        end_distance = (
            observed_after.get("distance")
            if observed_after is not None
            else distance_between_positions(end_position, target_position)
        )

        result = {
            **target_result,
            "item_name": item_name,
            "target_position": target_position,
            "start_position": before["position"],
            "end_position": end_position,
            "start_distance": target.get("distance"),
            "end_distance": end_distance,
            "target_observed_after": observed_after,
            "inventory_count_before": before_count,
            "inventory_count_after": after_count,
            "inventory_count_delta": after_count - before_count,
            "move_result": move_result,
        }

        if after_count <= before_count:
            return False, {
                **result,
                "error": "pickup_not_confirmed",
            }

        return True, {
            **result,
            "reason": "inventory_count_increased",
        }
