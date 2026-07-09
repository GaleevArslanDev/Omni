"""Central runtime settings for the Omni agent.

Keep short, practical comments here near the values.
Longer explanations and setup guidance belong in README/docs.
"""

# LLM settings used for the high-level reasoning loop.
LLM_MODEL = "qwen3:8b"
LLM_TEMPERATURE = 0
LLM_NUM_PREDICT = 1000

# Hard limit for sequential agent steps in one run.
AGENT_MAX_STEPS = 20

# Minecraft bot connection settings.
MINECRAFT_USERNAME = "Omni"
MINECRAFT_HOST = "localhost"
MINECRAFT_PORT = 3000
# None means Mineflayer chooses the protocol version automatically.
MINECRAFT_VERSION = None
MINECRAFT_HIDE_ERRORS = False

# Headless debug stream shown by the companion viewer.
DEBUG_STREAM_ENABLED = True
DEBUG_STREAM_HOST = "127.0.0.1"
DEBUG_STREAM_PORT = 8089
DEBUG_STREAM_WIDTH = 640
DEBUG_STREAM_HEIGHT = 360
# -1 means "stream indefinitely".
DEBUG_STREAM_FRAMES = -1

# Blocks the agent actively scans for in the nearby world model.
OBSERVED_BLOCK_NAMES = (
    "oak_log",
    "birch_log",
    "spruce_log",
    "crafting_table",
    "chest",
    "furnace",
    "coal_ore",
    "iron_ore",
    "water",
    "lava",
)
# Search radius for important nearby objects.
OBSERVED_BLOCK_RADIUS = 12
# Per block type cap returned by Mineflayer block search.
OBSERVED_BLOCK_MAX_PER_TYPE = 5
# Final cap after all nearby objects are merged and distance-sorted.
MAX_NEARBY_OBJECTS = 20

# Blocks used only for the coarse ground summary in observations.
GROUND_BLOCK_NAMES = (
    "grass_block",
    "dirt",
    "stone",
    "sand",
)
GROUND_BLOCK_RADIUS = 4
GROUND_BLOCK_MAX_PER_TYPE = 10

# Max distance for the block directly under the cursor in observations.
BLOCK_AT_CURSOR_MAX_DISTANCE = 8
# Default interaction distance for digging.
DIG_BLOCK_MAX_DISTANCE = 4.5
# Max time to wait for Mineflayer digging callbacks.
DIG_TIMEOUT_SECONDS = 10
