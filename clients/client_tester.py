import time

from clients.minecraft.client import MinecraftClient

client = MinecraftClient()
time.sleep(1)
print(client.observe())
