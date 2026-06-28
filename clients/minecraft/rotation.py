import math
import threading

from javascript import require

import logger

vec3 = require("vec3")


class RotationMixin:
    def turn_by_degrees(self, degrees: float) -> None:
        """
        Поворачивает агента на заданное количество градусов относительно текущего взгляда.
        Положительные градусы — поворот ВПРАВО.
        Отрицательные градусы — поворот ВЛЕВО.
        Блокирует Python, пока поворот не завершится.
        """
        # 1. Переводим градусы в радианы (Minecraft использует радианы)
        radians_to_add = math.radians(degrees)

        # 2. Получаем текущие углы бота (yaw - по горизонтали, pitch - по вертикали)
        current_yaw = self.bot.entity.yaw
        current_pitch = self.bot.entity.pitch

        # 3. Вычисляем новый горизонтальный угол
        new_yaw = current_yaw - radians_to_add

        # 4. Блокируем поток, пока бот физически поворачивает голову
        done = threading.Event()

        # Вызываем look(yaw, pitch, force=True для мгновенного или плавного изменения)
        # По умолчанию force=True выполняет поворот за 1 тик
        self.bot.look(new_yaw, current_pitch, True).then(lambda *args: done.set())

        done.wait()

    def look_at_coords(self, x: float, y: float, z: float) -> bool:
        try:
            self.bot.lookAt(vec3(x, y, z), True)
            success = True
        except Exception as e:
            logger.log_error(e)
            success = False

        return success
