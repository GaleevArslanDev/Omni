import math
from collections import Counter
from typing import Any

from javascript import require

import logger


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
                logger.log_error(e)
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
