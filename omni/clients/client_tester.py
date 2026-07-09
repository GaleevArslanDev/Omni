import time

from omni.clients.minecraft.client import MinecraftClient
from omni.tools import SayTool
from omni.tools.minecraft.look_at_nearest import LookAtNearestTool

client = MinecraftClient()
time.sleep(1)
while True:
    LookAtNearestTool().use(client, {"block_name": "oak_log"})
    if client.observe()["vision"]["block_at_cursor"]:
        SayTool().use(client, {"text": client.observe()["vision"]["block_at_cursor"]["name"]})
    else:
        SayTool().use(client, {"text": "none"})
    time.sleep(5)