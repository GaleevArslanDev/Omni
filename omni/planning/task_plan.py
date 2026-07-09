from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class TaskStep:
    id: str
    kind: str
    args: dict[str, Any]

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class TaskPlan:
    goal: str
    steps: list[TaskStep]

    def to_json(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "steps": [step.to_json() for step in self.steps],
        }
