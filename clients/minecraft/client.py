from javascript import terminate, On, require

from client_interface import ClientInterface
from clients.minecraft.chat import ChatMixin
from clients.minecraft.movement import MovementMixin
from clients.minecraft.observation import ObservationMixin
from clients.minecraft.rotation import RotationMixin

mineflayer = require("mineflayer")


class MinecraftClient(
    ObservationMixin,
    MovementMixin,
    RotationMixin,
    ChatMixin,
    ClientInterface,
):
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

    # --------------- UNUSABLE FUNCTIONS YET ---------------
    def execute(self, action: str, **kwargs) -> bool:
        pass

    def get_available_actions(self) -> list[str]:
        pass

    def reset(self) -> bool:
        pass
