import threading


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
