from javascript import terminate, On, require

from omni.clients.interface import ClientInterface
from omni.clients.minecraft.chat import ChatMixin
from omni.clients.minecraft.debug import DebugMixin
from omni.clients.minecraft.interaction import InteractionMixin
from omni.clients.minecraft.movement import MovementMixin
from omni.clients.minecraft.observation import ObservationMixin
from omni.clients.minecraft.rotation import RotationMixin

mineflayer = require("mineflayer")


class MinecraftClient(
    ObservationMixin,
    MovementMixin,
    RotationMixin,
    ChatMixin,
    InteractionMixin,
    DebugMixin,
    ClientInterface,
):
    def __init__(
        self,
        name="Omni",
        host="localhost",
        port=3000,
        version=None,
        hide_errors=False,
        debug_stream_host="127.0.0.1",
        debug_stream_port=8089,
        debug_stream_width=640,
        debug_stream_height=360,
        enable_debug_stream=True,
    ):
        self.bot_params = {
            "username": name,
            "host": host,
            "port": port,
            "hideErrors": hide_errors,
        }
        if version:
            self.bot_params["version"] = version
        if enable_debug_stream:
            self.init_debug_stream(
                host=debug_stream_host,
                port=debug_stream_port,
                width=debug_stream_width,
                height=debug_stream_height,
                frames=-1,
            )
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

        @On(self.bot, "spawn")
        def spawn(*args):
            self.start_debug_stream()

    def stop(self):
        self.stop_debug_stream()
        if self.bot:
            self.bot.quit()  # Отключаем бота от сервера Minecraft
        terminate()
