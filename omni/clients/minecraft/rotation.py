import math
import logging
import threading

from javascript import require

vec3 = require("vec3")
logger = logging.getLogger(__name__)


class RotationMixin:
    def turn_by_degrees(self, degrees: float) -> bool:
        try:
            radians_to_add = math.radians(degrees)

            current_yaw = self.bot.entity.yaw
            current_pitch = self.bot.entity.pitch

            new_yaw = current_yaw - radians_to_add

            result = self.bot.look(new_yaw, current_pitch, True)

            # Иногда jspybridge возвращает promise, иногда None.
            if result is not None and hasattr(result, "then"):
                done = threading.Event()
                result.then(lambda *args: done.set())
                done.wait(timeout=2)

            return True

        except Exception as e:
            logger.exception("Failed to turn by degrees")
            return False

    def look_at_coords(self, x: float, y: float, z: float) -> bool:
        try:
            self.bot.lookAt(vec3(x, y, z), True)
            success = True
        except Exception as e:
            logger.exception("Failed to look at coordinates")
            success = False

        return success
