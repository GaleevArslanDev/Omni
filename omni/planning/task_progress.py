from dataclasses import asdict, dataclass
from typing import Any, Literal

from omni.planning.progress_handlers import (
    update_progress_from_action,
    update_progress_from_observation,
)
from omni.planning.task_plan import TaskPlan, TaskStep
from omni.state.action import ActionEntry


@dataclass(slots=True)
class StepProgress:
    step_id: str
    status: Literal["pending", "done", "failed"] = "pending"
    evidence: str | None = None

    @property
    def done(self) -> bool:
        return self.status == "done"

    @property
    def failed(self) -> bool:
        return self.status == "failed"

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class TaskProgress:
    """
    v0.5 progress tracker.

    Не планнер.
    Не память.
    Не world model.
    Не LLM-written state.

    Это детерминированное состояние выполнения текущего TaskPlan.
    Обновляется только из observation и action log.
    """

    def __init__(self, plan: TaskPlan):
        self.plan = plan

        self.steps: dict[str, StepProgress] = {
            step.id: StepProgress(step_id=step.id)
            for step in plan.steps
        }

        self.remembered_objects: dict[str, dict[str, int]] = {}
        self.task_status: str = "running"  # running | done | failed
        self.failure_reason: str | None = None

    def current_step(self) -> TaskStep | None:
        if self.task_status != "running":
            return None

        for step in self.plan.steps:
            progress = self.steps[step.id]
            if progress.status == "pending":
                return step

            if progress.status == "failed":
                return None

        return None

    def mark_done(self, step_id: str, evidence: str) -> None:
        if step_id not in self.steps:
            return

        self.steps[step_id].status = "done"
        self.steps[step_id].evidence = evidence

        if all(progress.status == "done" for progress in self.steps.values()):
            self.task_status = "done"

    def mark_failed(self, step_id: str, evidence: str) -> None:
        if step_id not in self.steps:
            return

        self.steps[step_id].status = "failed"
        self.steps[step_id].evidence = evidence
        self.task_status = "failed"
        self.failure_reason = evidence

    def is_done(self) -> bool:
        return self.task_status == "done"

    def is_failed(self) -> bool:
        return self.task_status == "failed"

    def is_terminal(self) -> bool:
        return self.task_status in ("done", "failed")

    def update_from_observation(self, observation: dict, step_number: int) -> None:
        update_progress_from_observation(self, observation, step_number)

    def update_from_action(self, action: ActionEntry) -> None:
        update_progress_from_action(self, action)

    def to_json(self) -> dict[str, Any]:
        current = self.current_step()

        return {
            "task_status": self.task_status,
            "failure_reason": self.failure_reason,
            "current_step": current.to_json() if current else None,
            "steps": {
                step_id: progress.to_json()
                for step_id, progress in self.steps.items()
            },
            "remembered_objects": self.remembered_objects,
            "all_done": self.is_done(),
            "failed": self.is_failed(),
            "terminal": self.is_terminal(),
        }
