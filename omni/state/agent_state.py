import json


class AgentState:
    def __init__(self, filename="agent_state.json"):
        self.position = None
        self.rotation = None
        self.health = None
        self.food = None
        self.selected_slot = None
        self.main_hand = None
        self.inventory_summary = {}
        self.inventory_slots = {}
        self.filename = filename

    def save(self):
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(self.to_json(), f, indent=4, ensure_ascii=False)

    def update_from_observation(self, observation: dict, step: int):
        inv = observation["inventory"]
        self.position = observation["position"]
        self.rotation = observation["rotation"]
        self.health = observation["health"]
        self.food = observation["food"]
        self.selected_slot = inv["selected_slot"]
        self.main_hand = inv["main_hand"]
        self.inventory_summary = inv["summary"]
        self.inventory_slots = {
            "hotbar": inv["hotbar"],
            "main_inventory": inv["main_inventory"],
            "offhand": inv["offhand"],
            "armor": inv["armor"],
        }

        self.save()

    def to_json(self):
        data = self.__dict__.copy()
        data.pop('filename', None)
        return data
