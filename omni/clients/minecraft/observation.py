import logging
import math
from collections import Counter
from typing import Any

from javascript import require

from omni.config import (
    BLOCK_AT_CURSOR_MAX_DISTANCE,
    FRIENDLY_ENTITY_NAMES,
    GROUND_BLOCK_MAX_PER_TYPE,
    GROUND_BLOCK_NAMES,
    GROUND_BLOCK_RADIUS,
    HOSTILE_ENTITY_NAMES,
    IGNORED_ENTITY_NAMES,
    IGNORED_ENTITY_TYPES,
    MAX_DROPPED_ITEMS,
    MAX_NEARBY_ENTITIES,
    MAX_NEARBY_VEHICLES,
    MAX_NEARBY_OBJECTS,
    NEUTRAL_ENTITY_NAMES,
    OBSERVED_BLOCK_MAX_PER_TYPE,
    OBSERVED_BLOCK_NAMES,
    OBSERVED_BLOCK_RADIUS,
    OBSERVED_ENTITY_RADIUS,
    UTILITY_ENTITY_NAMES,
    VEHICLE_ENTITY_NAMES,
)

logger = logging.getLogger(__name__)


class ObservationMixin:
    def observe(self) -> dict[str, Any]:
        pos = self.bot.entity.position

        objects = self.get_blocks_by_names(
            names=list(OBSERVED_BLOCK_NAMES),
            radius=OBSERVED_BLOCK_RADIUS,
            max_per_type=OBSERVED_BLOCK_MAX_PER_TYPE,
        )

        ground = self.get_blocks_by_names(
            names=list(GROUND_BLOCK_NAMES),
            radius=GROUND_BLOCK_RADIUS,
            max_per_type=GROUND_BLOCK_MAX_PER_TYPE,
        )

        cursor_block = self.bot.blockAtCursor(BLOCK_AT_CURSOR_MAX_DISTANCE)

        inventory = self.get_inventory()
        entities = self.get_nearby_entities()

        return {
            "position": {
                "x": round(pos.x, 2),
                "y": round(pos.y, 2),
                "z": round(pos.z, 2),
            },
            "rotation": {
                "yaw": round(math.degrees(self.bot.entity.yaw), 2),
                "pitch": round(math.degrees(self.bot.entity.pitch), 2),
            },
            "health": self.bot.health,
            "food": self.bot.food,
            "inventory": inventory,
            "entities": entities,
            "vision": {
                "nearby_objects": objects[:MAX_NEARBY_OBJECTS],
                "ground_summary": dict(Counter(block["name"] for block in ground)),
                "block_at_cursor": self.serialize_block(cursor_block),
            }
        }

    def get_blocks_by_names(
        self,
        names: list[str],
        radius: int = OBSERVED_BLOCK_RADIUS,
        max_per_type: int = OBSERVED_BLOCK_MAX_PER_TYPE,
    ) -> list[dict]:
        mc_data = require("minecraft-data")(self.bot.version)
        result = []
        bot_pos = self.bot.entity.position

        blocks_by_name = mc_data.blocksByName

        for name in names:
            try:
                block_data = blocks_by_name[name]
                block_id = int(block_data.id)
            except Exception:
                logger.exception("Failed to resolve minecraft block data for %s", name)
                continue

            positions = self.bot.findBlocks({
                "matching": block_id,
                "maxDistance": radius,
                "count": max_per_type,
            })

            for p in positions:
                block = self.bot.blockAt(p)
                if block is None:
                    continue

                dx = block.position.x - bot_pos.x
                dy = block.position.y - bot_pos.y
                dz = block.position.z - bot_pos.z
                distance = math.sqrt(dx * dx + dy * dy + dz * dz)

                result.append({
                    "name": block.name,
                    "x": int(block.position.x),
                    "y": int(block.position.y),
                    "z": int(block.position.z),
                    "distance": round(distance, 2),
                })

        result.sort(key=lambda b: b["distance"])
        return result

    def get_nearby_entities(
        self,
        radius: int = OBSERVED_ENTITY_RADIUS,
        max_nearby: int = MAX_NEARBY_ENTITIES,
        max_dropped_items: int = MAX_DROPPED_ITEMS,
        max_vehicles: int = MAX_NEARBY_VEHICLES,
    ) -> dict[str, Any]:
        bot_pos = self.bot.entity.position

        try:
            raw_entities = self._collect_raw_entities()
        except Exception:
            logger.exception("Failed to collect nearby entities from Mineflayer")
            raw_entities = []

        nearby: list[dict[str, Any]] = []
        dropped_items: list[dict[str, Any]] = []
        vehicles: list[dict[str, Any]] = []

        for entity in raw_entities:
            position = entity.get("position")
            name = entity.get("name")
            entity_type = entity.get("entity_type")

            if not position or name is None:
                continue

            dx = float(position["x"]) - bot_pos.x
            dy = float(position["y"]) - bot_pos.y
            dz = float(position["z"]) - bot_pos.z
            distance = math.sqrt(dx * dx + dy * dy + dz * dz)

            if distance > radius:
                continue

            bucket = self._classify_entity_bucket(name=name, entity_type=entity_type)
            if bucket == "ignored":
                continue

            serialized = self.serialize_entity(
                entity=entity,
                distance=distance,
                bucket=bucket,
            )
            if serialized is None:
                continue

            if bucket == "nearby":
                nearby.append(serialized)
            elif bucket == "dropped_items":
                dropped_items.append(serialized)
            elif bucket == "vehicles":
                vehicles.append(serialized)

        nearby.sort(key=lambda entity: entity["distance"])
        dropped_items.sort(key=lambda entity: entity["distance"])
        vehicles.sort(key=lambda entity: entity["distance"])

        nearby = nearby[:max_nearby]
        dropped_items = dropped_items[:max_dropped_items]
        vehicles = vehicles[:max_vehicles]

        return {
            "nearby": nearby,
            "summary": dict(Counter(entity["name"] for entity in nearby)),
            "attitude_summary": dict(Counter(entity["attitude"] for entity in nearby)),
            "dropped_items": dropped_items,
            "dropped_items_summary": dict(
                Counter(
                    entity.get("item_name") or entity["name"]
                    for entity in dropped_items
                )
            ),
            "vehicles": vehicles,
            "vehicles_summary": dict(Counter(entity["name"] for entity in vehicles)),
        }

    def _collect_raw_entities(self) -> list[dict[str, Any]]:
        entities_proxy = getattr(self.bot, "entities", None)
        if entities_proxy is None:
            return []

        self_entity_id = getattr(getattr(self.bot, "entity", None), "id", None)
        result: list[dict[str, Any]] = []

        try:
            entity_keys = list(entities_proxy)
        except Exception:
            logger.exception("Failed to iterate bot.entities proxy")
            return []

        for entity_key in entity_keys:
            try:
                entity = entities_proxy[entity_key]
            except Exception:
                continue

            if entity is None:
                continue

            entity_id = getattr(entity, "id", None)
            if self_entity_id is not None and entity_id == self_entity_id:
                continue

            position = getattr(entity, "position", None)
            if position is None:
                continue

            item = getattr(entity, "item", None)
            if item is None and getattr(entity, "name", None) == "item":
                try:
                    item = entity.getDroppedItem()
                except Exception:
                    item = None

            result.append({
                "id": entity_id,
                "name": getattr(entity, "name", None),
                "display_name": getattr(entity, "displayName", None) or getattr(entity, "name", None),
                "entity_type": getattr(entity, "type", None),
                "position": {
                    "x": float(position.x),
                    "y": float(position.y),
                    "z": float(position.z),
                },
                "item_name": getattr(item, "name", None) if item is not None else None,
                "item_display_name": getattr(item, "displayName", None) if item is not None else None,
            })

        return result

    @staticmethod
    def _classify_entity_bucket(name: str, entity_type: str | None) -> str:
        if entity_type == "player":
            return "ignored"

        if name == "item":
            return "dropped_items"

        if name in VEHICLE_ENTITY_NAMES:
            return "vehicles"

        if name in IGNORED_ENTITY_NAMES:
            return "ignored"

        if entity_type in IGNORED_ENTITY_TYPES:
            return "ignored"

        if (
            name in HOSTILE_ENTITY_NAMES
            or name in NEUTRAL_ENTITY_NAMES
            or name in FRIENDLY_ENTITY_NAMES
            or name in UTILITY_ENTITY_NAMES
        ):
            return "nearby"

        if entity_type == "mob":
            return "nearby"

        return "ignored"

    @staticmethod
    def _classify_entity_attitude(name: str) -> str:
        if name in HOSTILE_ENTITY_NAMES:
            return "hostile"
        if name in NEUTRAL_ENTITY_NAMES:
            return "neutral"
        if name in FRIENDLY_ENTITY_NAMES:
            return "friendly"
        if name in UTILITY_ENTITY_NAMES:
            return "utility"
        return "unknown"

    @staticmethod
    def _classify_entity_kind(name: str, bucket: str) -> str:
        if bucket == "dropped_items":
            return "item"
        if bucket == "vehicles":
            return "vehicle"
        if name in UTILITY_ENTITY_NAMES:
            return "npc"
        return "mob"

    @staticmethod
    def serialize_block(block: Any) -> dict[str, Any] | None:
        if block is None:
            return None

        return {
            "name": block.name,
            "display_name": block.displayName,
            "position": {
                "x": int(block.position.x),
                "y": int(block.position.y),
                "z": int(block.position.z),
            },
            "diggable": bool(block.diggable),
            "transparent": bool(block.transparent),
        }

    @staticmethod
    def serialize_item(item: Any) -> dict[str, Any] | None:
        if item is None:
            return None

        return {
            "name": item.name,
            "display_name": item.displayName,
            "count": int(item.count),
            "slot": int(item.slot),
            "stack_size": int(item.stackSize),
        }

    @classmethod
    def serialize_entity(
        cls,
        entity: dict[str, Any],
        distance: float,
        bucket: str,
    ) -> dict[str, Any] | None:
        position = entity.get("position")
        if position is None:
            return None

        item_name = entity.get("item_name")
        item_display_name = entity.get("item_display_name")

        primary_name = entity.get("name")
        primary_display_name = entity.get("display_name") or primary_name

        if bucket == "dropped_items" and item_name is not None:
            primary_name = item_name
            primary_display_name = item_display_name or item_name

        serialized = {
            "id": entity.get("id"),
            "name": primary_name,
            "display_name": primary_display_name,
            "kind": cls._classify_entity_kind(entity.get("name"), bucket),
            "position": {
                "x": round(float(position["x"]), 2),
                "y": round(float(position["y"]), 2),
                "z": round(float(position["z"]), 2),
            },
            "distance": round(distance, 2),
        }

        if bucket == "nearby":
            serialized["attitude"] = cls._classify_entity_attitude(entity.get("name"))

        if bucket == "dropped_items":
            if item_name is not None:
                serialized["item_name"] = item_name
            if item_display_name is not None:
                serialized["item_display_name"] = item_display_name

        return serialized

    def get_inventory(self) -> dict[str, Any]:
        window = self.bot.inventory
        slots = window.slots

        quickbar_slot = getattr(self.bot, "quickBarSlot", None)
        selected_slot = int(quickbar_slot) if quickbar_slot is not None else None
        selected_slot_raw = 36 + selected_slot if selected_slot is not None else None

        held_item = self.serialize_item(getattr(self.bot, "heldItem", None))

        def safe_get_slot(slot_index: int) -> dict[str, Any] | None:
            try:
                return self.serialize_item(slots[slot_index])
            except Exception:
                return None

        def serialize_slot_range(start: int, end_inclusive: int) -> list[dict[str, Any] | None]:
            result = []
            for slot_index in range(start, end_inclusive + 1):
                result.append(safe_get_slot(slot_index))
            return result

        hotbar = serialize_slot_range(36, 44)
        main_inventory = serialize_slot_range(9, 35)
        armor = serialize_slot_range(5, 8)
        offhand = safe_get_slot(45)

        summary: dict[str, int] = {}
        for slot_index in range(9, 46):
            item = safe_get_slot(slot_index)
            if item is None:
                continue

            name = item["name"]
            summary[name] = summary.get(name, 0) + item["count"]

        return {
            "selected_slot": selected_slot,
            "selected_slot_raw": selected_slot_raw,
            "main_hand": held_item,
            "hotbar": hotbar,
            "main_inventory": main_inventory,
            "armor": armor,
            "offhand": offhand,
            "summary": summary,
        }
