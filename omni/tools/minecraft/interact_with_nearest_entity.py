from omni.clients.minecraft.client import MinecraftClient
from omni.config import DEFAULT_ENTITY_INTERACTION_RANGE
from omni.helpers.entity_targeting import (
    distance_between_positions,
    find_entity_by_id,
    get_raw_bot_entity_by_id,
    select_nearest_entity_from_observation,
)
from omni.tools.base import Tool


class InteractWithNearestEntityTool(Tool):
    name = "interact_with_nearest_entity"
    description = (
        "Deterministically selects the nearest observed entity or vehicle and right-click interacts with it. "
        "It does not implement trading, mounting, feeding, or milking as verified scenarios."
    )
    args_schema = {
        "category": "string - one of: nearby, vehicles",
        "target_name": "string - optional entity or vehicle name to interact with",
        "attitude": "string - optional, one of: hostile, neutral, friendly, utility; only for category=nearby",
        "interaction_range": "float - optional distance threshold before moving closer",
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, dict]:
        category = arguments.get("category", "nearby")
        target_name = arguments.get("target_name")
        attitude = arguments.get("attitude")
        interaction_range = float(arguments.get("interaction_range", DEFAULT_ENTITY_INTERACTION_RANGE))

        if category == "dropped_items":
            return False, {
                "error": "dropped_items_require_pickup_nearest_item",
                "category": category,
                "target_name": target_name,
            }

        if category not in {"nearby", "vehicles"}:
            return False, {
                "error": "invalid_interaction_category",
                "category": category,
                "allowed_categories": ["nearby", "vehicles"],
            }

        before = client.observe()
        success, target_result = select_nearest_entity_from_observation(
            observation=before,
            category=category,
            target_name=target_name,
            attitude=attitude,
        )

        if not success:
            return False, target_result

        selected_before = target_result["target"]
        start_position = before["position"]
        move_result = None

        if float(selected_before.get("distance", 0)) > interaction_range:
            target_position = selected_before["position"]
            move_success, move_result = client.move_to_coordinates(
                target_position["x"],
                target_position["y"],
                target_position["z"],
            )
            if not move_success:
                after_failed_move = client.observe()
                return False, {
                    **target_result,
                    "error": "approach_failed_before_interaction",
                    "start_position": start_position,
                    "end_position": after_failed_move["position"],
                    "move_result": move_result,
                }

        before_interaction = client.observe()
        selected_after_move = find_entity_by_id(
            observation=before_interaction,
            category=category,
            entity_id=selected_before.get("id"),
        )

        if selected_after_move is None:
            success, refreshed_target_result = select_nearest_entity_from_observation(
                observation=before_interaction,
                category=category,
                target_name=target_name,
                attitude=attitude,
            )
            if not success:
                return False, {
                    **target_result,
                    "error": "target_lost_before_interaction",
                    "start_position": start_position,
                    "end_position": before_interaction["position"],
                    "move_result": move_result,
                }
            target_result = refreshed_target_result
            selected_after_move = refreshed_target_result["target"]

        selected_entity_id = selected_after_move.get("id")
        if selected_entity_id is None:
            return False, {
                **target_result,
                "error": "selected_entity_has_no_id",
                "selected_entity": selected_after_move,
                "start_position": start_position,
                "end_position": before_interaction["position"],
                "move_result": move_result,
            }

        raw_entity = get_raw_bot_entity_by_id(client.bot, selected_entity_id)
        if raw_entity is None:
            return False, {
                **target_result,
                "error": "raw_entity_not_found",
                "selected_entity": selected_after_move,
                "start_position": start_position,
                "end_position": before_interaction["position"],
                "move_result": move_result,
            }

        try:
            client.bot.activateEntity(raw_entity)
        except Exception as error:
            return False, {
                **target_result,
                "error": "interaction_error",
                "message": str(error),
                "selected_entity": selected_after_move,
                "start_position": start_position,
                "end_position": before_interaction["position"],
                "move_result": move_result,
            }

        after_interaction = client.observe()
        observed_after_interaction = find_entity_by_id(
            observation=after_interaction,
            category=category,
            entity_id=selected_entity_id,
        )
        end_distance = (
            observed_after_interaction.get("distance")
            if observed_after_interaction is not None
            else distance_between_positions(after_interaction["position"], selected_after_move["position"])
        )

        return True, {
            **target_result,
            "interacted_entity": selected_after_move,
            "target_observed_after_interaction": observed_after_interaction,
            "start_position": start_position,
            "interaction_position": before_interaction["position"],
            "end_position": after_interaction["position"],
            "start_distance": selected_before.get("distance"),
            "interaction_distance": selected_after_move.get("distance"),
            "end_distance": end_distance,
            "move_result": move_result,
            "reason": "activate_entity_called",
        }
