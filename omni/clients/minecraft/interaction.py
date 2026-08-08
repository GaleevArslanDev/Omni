import threading

from javascript import require

from omni.config import (
    BLOCK_AT_CURSOR_MAX_DISTANCE,
    DIG_BLOCK_MAX_DISTANCE,
    DIG_TIMEOUT_SECONDS,
    PLACE_BLOCK_FACE_OFFSETS,
    PLACE_BLOCK_TIMEOUT_SECONDS,
)

Vec3 = require("vec3").Vec3


class InteractionMixin:
    def dig_block_at_cursor(
        self,
        max_distance: float = DIG_BLOCK_MAX_DISTANCE,
        expected_name: str | None = None,
    ) -> tuple[bool, dict]:
        target_block = self.bot.blockAtCursor(max_distance)

        if target_block is None or target_block.name == "air":
            return False, {
                "error": "no_block_at_cursor"
            }

        target_info = self.serialize_block(target_block)

        if expected_name is not None and target_info["name"] != expected_name:
            return False, {
                "error": "unexpected_block_at_cursor",
                "expected": expected_name,
                "actual": target_info["name"],
                "actual_block": target_info,
            }

        done = threading.Event()
        state = {
            "success": False,
            "error": None,
        }

        def cleanup():
            try:
                self.bot.removeListener("diggingCompleted", on_dig_complete)
                self.bot.removeListener("diggingAborted", on_dig_aborted)
            except Exception:
                pass
            done.set()

        def on_dig_complete(js_block=None, *args):
            state["success"] = True
            cleanup()

        def on_dig_aborted(js_block=None, *args):
            state["success"] = False
            state["error"] = "digging_aborted"
            cleanup()

        self.bot.on("diggingCompleted", on_dig_complete)
        self.bot.on("diggingAborted", on_dig_aborted)

        try:
            self.bot.dig(target_block)
        except Exception as e:
            state["success"] = False
            state["error"] = str(e)
            cleanup()

        finished = done.wait(timeout=DIG_TIMEOUT_SECONDS)

        if not finished:
            try:
                self.bot.removeListener("diggingCompleted", on_dig_complete)
                self.bot.removeListener("diggingAborted", on_dig_aborted)
            except Exception:
                pass

            return False, {
                "error": "dig_timeout",
                "target_block": target_info,
            }

        after_cursor = self.serialize_block(self.bot.blockAtCursor(max_distance))

        return state["success"], {
            "dug_block": target_info,
            "block_at_cursor_after": after_cursor,
            "error": state["error"],
        }

    def place_block_at_cursor(
        self,
        face: str = "top",
        max_distance: float = BLOCK_AT_CURSOR_MAX_DISTANCE,
        expected_item_name: str | None = None,
    ) -> tuple[bool, dict]:
        reference_block = self.bot.blockAtCursor(max_distance)

        if reference_block is None or reference_block.name == "air":
            return False, {
                "error": "no_reference_block",
            }

        face_offset = PLACE_BLOCK_FACE_OFFSETS.get(face)
        if face_offset is None:
            return False, {
                "error": "invalid_face",
                "provided_face": face,
            }
        face_vector = Vec3(*face_offset)

        held_item = getattr(self.bot, "heldItem", None)
        held_item_info = self.serialize_item(held_item)
        if held_item is None:
            return False, {
                "error": "empty_main_hand",
                "reference_block": self.serialize_block(reference_block),
            }

        if expected_item_name is not None and held_item.name != expected_item_name:
            return False, {
                "error": "unexpected_item_in_hand",
                "expected_item_name": expected_item_name,
                "actual_item_name": held_item.name,
                "reference_block": self.serialize_block(reference_block),
            }

        mc_data = require("minecraft-data")(self.bot.version)
        if held_item.name not in mc_data.blocksByName:
            return False, {
                "error": "item_in_hand_is_not_placeable",
                "item_name": held_item.name,
                "reference_block": self.serialize_block(reference_block),
            }

        target_position = reference_block.position.offset(face_vector.x, face_vector.y, face_vector.z)
        target_block_before = self.bot.blockAt(target_position)
        target_block_before_info = self.serialize_block(target_block_before)
        if target_block_before is not None and target_block_before.name != "air":
            return False, {
                "error": "target_position_occupied",
                "reference_block": self.serialize_block(reference_block),
                "target_block_before": target_block_before_info,
                "face": face,
            }

        done = threading.Event()
        state = {
            "success": False,
            "error": None,
            "placed_block": None,
        }

        def cleanup():
            try:
                self.bot.removeListener("blockPlaced", on_block_placed)
            except Exception:
                pass
            done.set()

        def on_block_placed(old_block=None, new_block=None, *args):
            candidate = new_block or old_block
            if candidate is None:
                return

            candidate_pos = candidate.position
            if (
                int(candidate_pos.x) != int(target_position.x)
                or int(candidate_pos.y) != int(target_position.y)
                or int(candidate_pos.z) != int(target_position.z)
            ):
                return

            state["success"] = True
            state["placed_block"] = self.serialize_block(candidate)
            cleanup()

        def on_place_rejected(*args):
            state["success"] = False
            state["error"] = "place_rejected"
            cleanup()

        self.bot.on("blockPlaced", on_block_placed)

        try:
            place_promise = self.bot.placeBlock(reference_block, face_vector)
            try:
                place_promise.catch(on_place_rejected)
            except Exception:
                pass
        except Exception as e:
            state["success"] = False
            state["error"] = f"js_execution_error: {e}"
            cleanup()

        finished = done.wait(timeout=PLACE_BLOCK_TIMEOUT_SECONDS)

        if finished and not state["success"] and state["error"] is not None:
            return False, {
                "error": state["error"],
                "reference_block": self.serialize_block(reference_block),
                "target_block_before": target_block_before_info,
                "face": face,
                "held_item": held_item_info,
            }

        if not finished:
            try:
                self.bot.removeListener("blockPlaced", on_block_placed)
            except Exception:
                pass

            target_block_after = self.serialize_block(self.bot.blockAt(target_position))
            return False, {
                "error": "place_timeout",
                "reference_block": self.serialize_block(reference_block),
                "target_block_before": target_block_before_info,
                "target_block_after": target_block_after,
                "face": face,
                "held_item": held_item_info,
            }

        current_main_hand = self.serialize_item(getattr(self.bot, "heldItem", None))

        return state["success"], {
            "reference_block": self.serialize_block(reference_block),
            "target_position": {
                "x": int(target_position.x),
                "y": int(target_position.y),
                "z": int(target_position.z),
            },
            "target_block_before": target_block_before_info,
            "placed_block": state["placed_block"],
            "face": face,
            "held_item_before": held_item_info,
            "held_item_after": current_main_hand,
            "expected_item_name": expected_item_name,
            "error": state["error"],
        }
