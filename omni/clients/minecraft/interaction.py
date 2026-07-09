import threading

from omni.config import DIG_BLOCK_MAX_DISTANCE, DIG_TIMEOUT_SECONDS


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
