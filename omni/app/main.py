from omni.app.runner import run_agent_loop
from omni.clients.minecraft.client import MinecraftClient
from omni.config.logging_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    client = MinecraftClient()
    goal = input("> ")
    run_agent_loop(client, goal)
