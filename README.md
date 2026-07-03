# Omni

Omni is a Python-based autonomous Minecraft agent that connects to a Minecraft server, observes the surrounding world, leverages a Local LLM for cognitive decision-making, and executes actions through a deterministic task-tracking and tool system.

The project combines:
- A **Mineflayer-backed** Minecraft client (Python-to-Node bridge),
- An **Ollama-powered** cognitive loop,
- A **deterministic task planner** and execution progress tracker,
- A **modular tool registry** for autonomous movement, vision, communication, and block interaction.

## Ecosystem & Companion Apps

- **[Minecraft World Model Viewer](https://github.com/GaleevArslanDev/omni-world-state-visualizer)** — A dedicated Panda3D desktop companion application used to monitor and visualize Omni's live `world_state.json` updates in real-time.

## How It Works

On each step, the agent execution loop:
1. Observes the world coordinates and environment around it.
2. Updates the internal `WorldState` and evaluates `TaskProgress`.
3. Constructs a contextual prompt for the Local LLM using observation, action history, `WorldState`, `TaskPlan`, and `TaskProgress`.
4. Receives exactly one tool call response formatted in JSON.
5. Executes the selected tool via the registry.
6. Captures post-action observation and computes `observation_diff`.
7. Updates `WorldState` and `TaskProgress` from tool results and action history.
8. Continues until the objective becomes terminal or the step limit is reached.

The current toolset allows the agent to handle tasks such as:
- Moving forward for a fixed duration.
- Changing body orientation (turning left/right).
- Locking gaze at specific coordinates or nearby blocks.
- Broadcasting text updates in the game chat.
- Mining the specific block currently under the crosshair.
- Tracking and recalling object locations for multi-step goals.
- Verifying target alignment before digging.
- Enforcing expected-block digging and deterministic failure on target mismatch.
- Reporting observed world changes after successful object interaction.

## Architecture & Project Structure

```text
.
|-- main.py                     # Agent entry point and execution loop
|-- llm.py                      # Ollama API call wrapper
|-- prompt.py                   # Prompt construction and context engineering
|-- tool_registry.py            # Tool lookup and execution management
|-- tools_loader.py             # Automatic runtime tool discovery
|-- task_plan.py                # Deterministic task plan parsing
|-- task_progress.py            # Deterministic progress tracking layer
|-- world_state.py              # Persistent observed world state memory
|-- clients/
|   `-- minecraft/              # Mineflayer client bridge and capability mixins
`-- tools/
    |-- common/                 # Shared core tools (e.g., done)
    `-- minecraft/              # Minecraft-specific action implementations
```

## Core Milestones (Version History)

- **`v0.6.0` (Current)**: Hardened object interaction with explicit target flow, look-at verification, expected-block digging, deterministic reporting, and stricter controller termination.
- **`v0.5.0`**: Transitioned task logic to a strict algorithmic layer, isolating execution tracking from LLM hallucination.
- **`v0.4.0`**: Introduced the `WorldState` persistence memory layer and offloaded delta observation tracking away from the LLM context.
- **`v0.3.0`**: Implemented core environment interaction via the `digging` tool registry.
- **`v0.2.0`**: Added spatial block-scanning capabilities and surrounding world perception.
- **`v0.1.0`**: Configured basic locomotion, physics-based 3D rotation, and movement.
- **`v0.0.0`**: Initial text-based agent architecture framework.

## Requirements

- Python 3.10+
- Node.js
- Active Minecraft Java server (recommended version `1.20.1`)
- Locally installed [Ollama](https://ollama.com) instance
- The `qwen3:8b` model available via Ollama

*Note: The repository currently does not include a `requirements.txt` or `package.json`. Node and Python dependencies must be fetched manually.*

## Setup

### 1. Install Dependencies
Install the required Python packages and the Node bridge:
```bash
pip install ollama javascript
npm install mineflayer prismarine-viewer canvas node-canvas-webgl
```

### 2. Fetch the Local LLM
Ensure your local Ollama instance is active and download the model specified in `llm.py`:
```bash
ollama pull qwen3:8b
```

### 3. Server Configuration
By default, the client in `clients/minecraft/client.py` connects using the following parameters:
- **Host**: `localhost`
- **Port**: `3000`
- **Version**: `1.20.1`
- **Username**: `Omni`

Modify this configuration file directly if your Minecraft server uses alternative connection tokens.

## Running the Agent

Launch the main cognitive loop:
```bash
python main.py
```
Type your goal directly into the console prompt when requested. 

**Example Prompts:**
- *“Move forward for 3 seconds”*
- *“Remember the chest, move forward for 2 seconds, and tell me where the chest was”*
- *“Turn to the oak_log, break it, and say what changed”*

## Current Development Notes

- **Language Stance**: Some core prompt configurations and internal planner evaluation text are written in Russian, though the execution runtime layer remains completely language-agnostic.
- **Observation Flow**: The standalone `observe` tool class is temporarily disabled; environment data extraction is handled natively by the core loop orchestration.
- **Task Planning Scope**: `TaskPlan` is intentionally narrow. It supports a small set of deterministic templates rather than acting as a general planner.
- **Interaction Semantics**: `remember_object_location` means "remember the nearest observed object of the requested type", not every object of that type.
- **Step Limit**: To prevent runaway API costs or infinite loops, the agent is hardcoded to terminate after 20 sequential tool steps.

## Limitations & Next Steps

- Missing dependency lockfiles (`requirements.txt`, `package.json`).
- Absence of automated testing suites.
- The deterministic planner currently accommodates only a restricted set of sequence patterns.
- `report_observation_diff` still relies on LLM wording constrained by prompt rules rather than a fully structured reporting tool.
- Connection configurations are static and hardcoded within source files.
