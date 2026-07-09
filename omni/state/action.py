from dataclasses import dataclass, asdict
from typing import Any


@dataclass(slots=True)
class ActionEntry:
    step: int
    tool: str
    arguments: dict[str, Any]
    success: bool
    result: Any
    observation_diff: Any = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)
