from dataclasses import dataclass, asdict
from typing import Any


@dataclass(slots=True)
class MemoryEntry:
    step: int
    text: str

    def to_json(self) -> dict[str, Any]:
        return asdict(self)
