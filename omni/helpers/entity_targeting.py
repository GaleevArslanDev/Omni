from typing import Any


ENTITY_CATEGORIES = {"nearby", "dropped_items", "vehicles"}


def _matches_target_name(entity_name: str | None, target_name: str) -> bool:
    if entity_name == target_name:
        return True

    if target_name == "boat":
        return entity_name is not None and (
            entity_name.endswith("_boat")
            or entity_name.endswith("_raft")
        )

    if target_name == "minecart":
        return entity_name is not None and entity_name.endswith("_minecart")

    return False


def select_nearest_entity_from_observation(
    observation: dict[str, Any],
    category: str = "nearby",
    target_name: str | None = None,
    attitude: str | None = None,
) -> tuple[bool, dict[str, Any]]:
    if category not in ENTITY_CATEGORIES:
        return False, {
            "error": "invalid_entity_category",
            "category": category,
            "allowed_categories": sorted(ENTITY_CATEGORIES),
        }

    if category != "nearby" and attitude is not None:
        return False, {
            "error": "attitude_filter_requires_nearby_category",
            "category": category,
            "attitude": attitude,
        }

    entities = observation.get("entities", {})
    candidates = list(entities.get(category, []))

    if target_name is not None:
        candidates = [
            entity for entity in candidates
            if _matches_target_name(entity.get("name"), target_name)
        ]

    if attitude is not None:
        candidates = [
            entity for entity in candidates
            if entity.get("attitude") == attitude
        ]

    if not candidates:
        return False, {
            "error": "entity_not_found",
            "category": category,
            "target_name": target_name,
            "attitude": attitude,
        }

    target = min(candidates, key=lambda entity: float(entity.get("distance", 0)))

    return True, {
        "category": category,
        "target_name": target_name,
        "attitude": attitude,
        "target": target,
    }
