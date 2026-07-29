import threading

from javascript import require

from omni.config import MOVE_TO_COORDINATES_TIMEOUT_SECONDS

mineflayer_pathfinder = require("mineflayer-pathfinder")


def _normalize_path_reset_reason(reason) -> str:
    if isinstance(reason, str):
        return reason

    return "path_reset"


class MovementMixin:
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

    def move_to_coordinates(self, x, y, z) -> tuple[bool, dict]:
        """
        Безопасное перемещение к координатам с защитой от застревания.

        Возвращает:
        - success=True, если цель достигнута
        - success=False и details["error"], если произошел timeout или path_reset
        """
        done = threading.Event()
        goal = mineflayer_pathfinder.goals.GoalNear(x, y, z, 1)

        state = {
            "success": False,
            "reason": None,
        }
        cleaned_up = False

        def cleanup():
            nonlocal cleaned_up
            if cleaned_up:
                return

            cleaned_up = True

            try:
                self.bot.removeListener("goal_reached", on_success)
                self.bot.removeListener("path_reset", on_fail)
            except Exception:
                pass

            try:
                self.bot.pathfinder.setGoal(None)
            except Exception:
                pass

            done.set()

        def on_success(*args):
            state["success"] = True
            state["reason"] = "goal_reached"
            cleanup()

        def on_fail(reason=None, *args):
            state["success"] = False
            state["reason"] = _normalize_path_reset_reason(reason)
            cleanup()

        self.bot.on("goal_reached", on_success)
        self.bot.on("path_reset", on_fail)

        try:
            self.bot.pathfinder.setGoal(goal)
        except Exception:
            state["success"] = False
            state["reason"] = "set_goal_error"
            cleanup()
            return False, {
                "error": "set_goal_error",
                "reason": "set_goal_error",
            }

        completed = done.wait(MOVE_TO_COORDINATES_TIMEOUT_SECONDS)

        if not completed:
            state["success"] = False
            state["reason"] = "timeout"
            cleanup()
            return False, {
                "error": "move_timeout",
                "reason": "timeout",
            }

        if state["success"]:
            return True, {
                "reason": state["reason"],
            }

        return False, {
            "error": "path_reset",
            "reason": state["reason"],
        }
