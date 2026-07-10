# Omni

Omni is a Python-based autonomous Minecraft agent that connects to a Minecraft server, observes both the world and its own runtime state, uses a local LLM for high-level reasoning, and executes actions through a deterministic task and tool layer.

The project currently combines:
- A Mineflayer-backed Minecraft client through a Python-to-Node bridge
- An Ollama-powered reasoning loop
- A deterministic `TaskPlan` / `TaskProgress` layer for supported multi-step goals
- A persistent `WorldState` for observed world objects
- A separate `AgentState` for the agent's own state
- A modular tool registry for movement, rotation, chat, targeting, digging, self-state reporting, and basic hotbar control

## Ecosystem & Companion Apps

- [Minecraft World Model Viewer](https://github.com/GaleevArslanDev/omni-world-state-visualizer) - a dedicated Panda3D desktop companion app used to monitor and visualize live debug stream, `agent_state.json` and `world_state.json` updates

## How It Works

On each step, the agent execution loop:
1. Observes the environment and the agent's own state.
2. Updates `WorldState`, `AgentState`, and `TaskProgress`.
3. Builds a prompt from the current observation, action history, memory, `WorldState`, and `AgentState`.
4. If the current task step is deterministic, executes it directly from `TaskPlan` / `TaskProgress`.
5. Otherwise receives exactly one JSON tool call from the local LLM.
6. Executes the resulting tool through the registry.
7. Captures a post-action observation and computes `observation_diff`.
8. Updates `WorldState` and `TaskProgress` from the action result and observed delta.
9. Stops when the task becomes terminal, the LLM uses `done`, or the step limit is reached.

## Architecture & Project Structure

```text
.
|-- omni/
|   |-- app/                    # Entry point, main loop, observation diff helpers
|   |-- clients/                # Client interface and Minecraft implementation
|   |   `-- minecraft/          # Mineflayer bridge and capability mixins
|   |-- config/                 # Runtime settings and logging setup
|   |-- llm/                    # Ollama client and safe JSON wrapper
|   |-- planning/               # Deterministic planning and progress tracking
|   |-- prompt/                 # Prompt builder and prompt sections
|   |-- state/                  # Action log, world state, agent state, memory
|   `-- tools/                  # Tool registry and tool implementations
|       |-- common/
|       `-- minecraft/
|-- requirements.txt            # Python dependencies
|-- pyproject.toml              # Basic project metadata
|-- package.json                # Node dependencies for Mineflayer / viewer stack
`-- README.md
```

## Current State

The repository is currently at `v0.8.0` development state.

Main completed pieces:
- `WorldState` stores observed world objects across steps
- `AgentState` stores the agent's own position, rotation, health, food, selected slot, held item, and inventory snapshot
- Minecraft observations include both `vision` and `inventory`
- The agent can deterministically switch hotbar slots and select an item from hotbar by item name
- Deterministic planned execution no longer lets the LLM rewrite `use_tool` task arguments
- Remember/report and dig/report flows are now executed through a stronger deterministic controller path
- Prompt rules explicitly separate:
  - what the agent sees in the world
  - what the agent has or holds
  - what the deterministic task layer says is already done
- The deterministic planner supports a small set of known multi-step patterns and self-state questions

Still intentionally limited:
- Inventory interaction is currently limited to hotbar selection and holding an item already present in hotbar
- There is still no item transfer between arbitrary slots, chest handling, crafting, armor flow, or offhand automation
- The planner is deliberately narrow and is not meant to be a general-purpose planner yet

## Core Milestones

- **`v0.8.0` (Current)**: Turned inventory from passive knowledge into a first actionable layer through deterministic hotbar control and planned inventory execution
- `v0.7.0`: Introduced the self-state layer through `AgentState`, extended observations with inventory data, and taught the agent to reason about itself separately from the world
- `v0.6.0`: Hardened object interaction with explicit target flow, look-at verification, expected-block digging, deterministic reporting, and stricter controller termination
- `v0.5.0`: Transitioned task logic to a strict algorithmic layer, isolating execution tracking from LLM hallucination
- `v0.4.0`: Introduced the `WorldState` persistence memory layer and offloaded observation-difference tracking away from the LLM context
- `v0.3.0`: Implemented core environment interaction via the digging tool registry
- `v0.2.0`: Added surrounding world perception
- `v0.1.0`: Configured basic locomotion, rotation, and movement
- `v0.0.0`: Initial text-based agent framework

## Requirements

- Python 3.10+
- Node.js
- Active Minecraft Java server
- Locally installed [Ollama](https://ollama.com)
- The model configured in `omni/config/settings.py`

## Setup

### 1. Install Dependencies

Install Python and Node dependencies:

```bash
pip install -r requirements.txt
npm install
```

### 2. Fetch the Local LLM

Ensure your local Ollama instance is active and download the model configured in `omni/config/settings.py`:

```bash
ollama pull qwen3:8b
```

### 3. Configure the Agent

Edit `omni/config/settings.py` if needed.

Important settings include:
- `LLM_MODEL`
- `AGENT_MAX_STEPS`
- `MINECRAFT_HOST`
- `MINECRAFT_PORT`
- `MINECRAFT_USERNAME`
- `DEBUG_STREAM_ENABLED`
- `OBSERVED_BLOCK_NAMES`

By default, the client connects with:
- Host: `localhost`
- Port: `3000`
- Username: `Omni`

`MINECRAFT_VERSION = None` means Mineflayer chooses the protocol version automatically.

## Running the Agent

Launch the main loop:

```bash
python -m omni.app.main
```

Type your goal directly into the console prompt when requested.

Example prompts:
- `Move forward for 3 seconds`
- `Remember the chest, move forward for 2 seconds, and tell me where the chest was`
- `Turn to the oak_log, break it, and say what changed`
- `Select slot 3`
- `Hold green_wool`
- `If you have green_wool, hold it`
- `What do you have in your inventory?`
- `How much health do you have?`

## Current Development Notes

- Language stance: some core prompt rules and planner-related text are written in Russian, while the runtime architecture itself is language-agnostic
- Observation flow: the standalone `observe` tool exists, but the main loop refreshes observations directly on each step
- Task planning scope: `TaskPlan` intentionally recognizes only a small set of deterministic patterns rather than acting as a general planner
- Interaction semantics: `remember_object_location` means "remember the nearest observed object of the requested type", not every object of that type
- Self-state semantics: `AgentState` is the source of truth for questions about the agent itself, including health, food, coordinates, held item, selected slot, and inventory contents
- Inventory action scope: `v0.8.0` only covers hotbar-level control, not full inventory manipulation
- Step limit: the agent stops after `AGENT_MAX_STEPS`, configured in `omni/config/settings.py`

## Limitations & Next Steps

- No automated test suite yet
- The deterministic planner currently supports only a restricted set of sequence patterns
- Full inventory manipulation beyond hotbar selection still does not exist
- Conditional inventory flows are intentionally narrow and only cover simple hotbar-dependent phrasing
- Runtime settings still live in a Python settings module, not in environment variables or a dedicated external config file
