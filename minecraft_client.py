import math
import threading
import time
from abc import ABC
from collections import Counter
from typing import Any

from javascript import require, On, Once, AsyncTask, once, off, terminate

from client_interface import ClientInterface

vec3 = require("vec3")
mineflayer = require("mineflayer")

class MinecraftClient(ClientInterface, ABC):
    def __init__(self, name="Omni", host="localhost", port=3000, version="1.20.1", hide_errors=False):
        self.bot_params = {"username": name, "host": host, "port": port, "version": version, "hideErrors": hide_errors}
        self.bot = None
        self._start_bot()

    def _start_bot(self) -> None:
        self.bot = mineflayer.createBot(self.bot_params)
        self._start_events()

    def _start_events(self) -> None:
        @On(self.bot, "login")
        def login(*args):
            pass

        @On(self.bot, "messagestr")
        def messagestr(*args):
            # message = args[0]
            #
            # words = message.split(" ")
            # if len(words) > 1:
            #     message_no_tag = " ".join(words[1:])
            # else:
            #     message_no_tag = message
            pass

    def stop(self):
        if self.bot:
            self.bot.quit()  # Отключаем бота от сервера Minecraft
        terminate()

    def set_control_state_for(self, action: str, secs: float) -> None:
        """
        Надежный инструмент движения для агента.
        Считает тики напрямую через событие игры и жестко блокирует Python до остановки.
        """
        total_ticks = int(secs * 20)
        ticks_passed = 0

        # Создаем событие для блокировки текущего потока Python
        done = threading.Event()

        # Зажимаем клавишу движения
        self.bot.setControlState(action, True)

        # Нам нужно объявить функцию-обработчик заранее, чтобы потом её удалить
        def on_tick(*args):
            nonlocal ticks_passed
            ticks_passed += 1

            # Если отсчитали нужные тики
            if ticks_passed >= total_ticks:
                # 1. Гарантированно выключаем управление
                self.bot.clearControlStates()
                # 2. Отписываемся от события, чтобы не спамить память
                self.bot.removeListener("physicsTick", on_tick)
                # 3. Даем сигнал Python, что можно идти дальше
                done.set()

        # Подписываемся на каждый игровой тик напрямую через объект бота
        self.bot.on("physicsTick", on_tick)

        # Ждем здесь, пока on_tick не вызовет done.set()
        done.wait()

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

    def say(self, text: str) -> None:
        self.bot.chat(text)

    def execute(self, action: str, **kwargs) -> bool:
        pass

    def get_available_actions(self) -> list[str]:
        pass

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
            except Exception:
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

    def serialize_block(self, block):
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

    def look_at_coords(self, x: float, y: float, z: float) -> bool:
        try:
            self.bot.lookAt(vec3(x, y, z), True)
            success = True
        except Exception as e:
            success = False

        return success

    def reset(self) -> bool:
        pass

# client = MinecraftClient()
# time.sleep(1)
# print(client.observe())