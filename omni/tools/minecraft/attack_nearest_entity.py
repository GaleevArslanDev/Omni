from typing import Any

from omni.clients.minecraft.client import MinecraftClient
from omni.config import DEFAULT_ENTITY_ATTACK_RANGE
from omni.helpers.entity_targeting import (
    distance_between_positions,
    find_entity_by_id,
    select_nearest_entity_from_observation,
)
from omni.tools.base import Tool


def _get_raw_bot_entity_by_id(bot: Any, entity_id: Any) -> Any | None:
    entities = getattr(bot, "entities", None)
    if entities is None:
        return None

    for key in (entity_id, str(entity_id)):
        try:
            entity = entities[key]
            if entity is not None:
                return entity
        except Exception:
            pass

    try:
        keys = list(entities)
    except Exception:
        return None

    for key in keys:
        try:
            entity = entities[key]
        except Exception:
            continue

        if getattr(entity, "id", None) == entity_id:
            return entity

    return None


class AttackNearestEntityTool(Tool):
    name = "attack_nearest_entity"
    description = (
        "Deterministically selects the nearest observed living entity and attacks it. "
        "If the entity is too far away, it first moves toward the entity through move_to_coordinates. "
        "It does not attack dropped items or vehicles."
    )
    args_schema = {
        "target_name": "string - optional living entity name to attack",
        "attitude": "string - optional, one of: hostile, neutral, friendly, utility",
        "attack_range": "float - optional distance threshold before moving closer",
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, dict]:
        target_name = arguments.get("target_name")
        attitude = arguments.get("attitude")
        attack_range = float(arguments.get("attack_range", DEFAULT_ENTITY_ATTACK_RANGE))

        before = client.observe()
        success, target_result = select_nearest_entity_from_observation(
            observation=before,
            category="nearby",
            target_name=target_name,
            attitude=attitude,
        )

        if not success:
            return False, target_result

        selected_before = target_result["target"]
        start_position = before["position"]
        move_result = None

        if float(selected_before.get("distance", 0)) > attack_range:
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
                    "error": "approach_failed_before_attack",
                    "start_position": start_position,
                    "end_position": after_failed_move["position"],
                    "move_result": move_result,
                }

        before_attack = client.observe()
        selected_after_move = find_entity_by_id(
            observation=before_attack,
            category="nearby",
            entity_id=selected_before.get("id"),
        )

        if selected_after_move is None:
            success, refreshed_target_result = select_nearest_entity_from_observation(
                observation=before_attack,
                category="nearby",
                target_name=target_name,
                attitude=attitude,
            )
            if not success:
                return False, {
                    **target_result,
                    "error": "target_lost_before_attack",
                    "start_position": start_position,
                    "end_position": before_attack["position"],
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
                "end_position": before_attack["position"],
                "move_result": move_result,
            }

        raw_entity = _get_raw_bot_entity_by_id(client.bot, selected_entity_id)
        if raw_entity is None:
            return False, {
                **target_result,
                "error": "raw_entity_not_found",
                "selected_entity": selected_after_move,
                "start_position": start_position,
                "end_position": before_attack["position"],
                "move_result": move_result,
            }

        try:
            client.bot.attack(raw_entity)
        except Exception as error:
            return False, {
                **target_result,
                "error": "attack_error",
                "message": str(error),
                "selected_entity": selected_after_move,
                "start_position": start_position,
                "end_position": before_attack["position"],
                "move_result": move_result,
            }

        after_attack = client.observe()
        observed_after_attack = find_entity_by_id(
            observation=after_attack,
            category="nearby",
            entity_id=selected_entity_id,
        )
        end_distance = (
            observed_after_attack.get("distance")
            if observed_after_attack is not None
            else distance_between_positions(after_attack["position"], selected_after_move["position"])
        )

        return True, {
            **target_result,
            "attacked_entity": selected_after_move,
            "target_observed_after_attack": observed_after_attack,
            "start_position": start_position,
            "attack_position": before_attack["position"],
            "end_position": after_attack["position"],
            "start_distance": selected_before.get("distance"),
            "attack_distance": selected_after_move.get("distance"),
            "end_distance": end_distance,
            "move_result": move_result,
            "reason": "attack_called",
        }
