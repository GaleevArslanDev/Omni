import json
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class WorldObject:
    id: str
    name: str
    position: dict[str, int]
    status: str
    first_seen_step: int
    last_seen_step: int
    removed_step: int | None = None

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class WorldState:
    def __init__(self, filename="world_state.json"):
        self.objects: dict[str, WorldObject] = {}
        self.filename = filename

    def save(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.to_json(), f, indent=4, ensure_ascii=False)

    def _make_id(self, name: str, position: dict) -> str:
        return f"{name}@{position['x']},{position['y']},{position['z']}"

    def update_from_observation(self, observation: dict, step: int):
        for obj in observation["vision"]["nearby_objects"]:
            pos = {"x": obj["x"], "y": obj["y"], "z": obj["z"]}
            obj_id = self._make_id(obj["name"], pos)

            if obj_id not in self.objects:
                self.objects[obj_id] = WorldObject(
                    id=obj_id,
                    name=obj["name"],
                    position=pos,
                    status="observed",
                    first_seen_step=step,
                    last_seen_step=step,
                )
            else:
                known = self.objects[obj_id]
                if known.status != "removed":
                    known.status = "observed"
                    known.last_seen_step = step

        self.save()

    def update_from_action(self, action):
        if action.tool == "dig_block_at_cursor" and action.success:
            result = action.result or {}
            dug = result.get("dug_block")

            if not dug:
                return

            pos = dug["position"]
            obj_id = self._make_id(dug["name"], pos)

            if obj_id in self.objects:
                self.objects[obj_id].status = "removed"
                self.objects[obj_id].removed_step = action.step
        self.save()

    def to_json(self):
        return [obj.to_json() for obj in self.objects.values()]
