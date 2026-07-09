from omni.planning.task_plan import TaskPlan
from omni.planning.task_progress import TaskProgress
from omni.prompt.sections import (
    render_action_log,
    render_agent_state,
    render_global_rules,
    render_intro,
    render_memory,
    render_response_format,
    render_task_state,
    render_tools,
    render_world_state,
)
from omni.state.action import ActionEntry
from omni.state.agent_state import AgentState
from omni.state.memory import MemoryEntry
from omni.state.world_state import WorldState


def create_prompt(
    goal: str,
    observations: dict,
    actions: list[ActionEntry],
    memory: list[MemoryEntry],
    world_state: WorldState,
    agent_state: AgentState,
    task_plan: TaskPlan,
    task_progress: TaskProgress,
    tools_description: str,
) -> str:
    sections = [
        render_intro(goal, observations),
        render_action_log(actions),
        render_world_state(world_state),
        render_agent_state(agent_state),
        render_task_state(task_plan, task_progress),
        render_memory(memory),
        render_tools(tools_description),
        render_response_format(),
        render_global_rules(),
    ]
    return "\n\n".join(sections).strip()
