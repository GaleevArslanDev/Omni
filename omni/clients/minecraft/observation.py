import math
import logging

from collections import Counter
from typing import Any

from javascript import require

logger = logging.getLogger(__name__)


class ObservationMixin:
    def observe(self) -> dict[str, Any]:
        pos = self.bot.entity.position

        objects = self.get_blocks_by_names(
            names=[
                "oak_log", "birch_log", "spruce_log",
                "crafting_table", "chest", "furnace",
                "coal_ore", "iron_ore",
                "water", "lava",
            ],
            radius=12,
            max_per_type=5,
        )

        ground = self.get_blocks_by_names(
            names=["grass_block", "dirt", "stone", "sand"],
            radius=4,
            max_per_type=10,
        )

        cursor_block = self.bot.blockAtCursor(8)

        inventory = self.get_inventory()

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
            "vision": {
                "nearby_objects": objects[:20],
                "ground_summary": dict(Counter(block["name"] for block in ground)),
                "block_at_cursor": self.serialize_block(cursor_block),
            }
        }

    def get_blocks_by_names(self, names: list[str], radius: int = 8, max_per_type: int = 5) -> list[dict]:
        mc_data = require("minecraft-data")(self.bot.version)
        result = []
        bot_pos = self.bot.entity.position

        blocks_by_name = mc_data.blocksByName

        for name in names:
            try:
                block_data = blocks_by_name[name]
                block_id = int(block_data.id)
            except Exception as e:
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
