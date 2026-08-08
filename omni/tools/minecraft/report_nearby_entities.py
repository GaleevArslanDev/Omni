from omni.clients.minecraft.client import MinecraftClient
from omni.config import ENTITY_ATTITUDE_LABELS
from omni.tools.base import Tool


class ReportNearbyEntitiesTool(Tool):
    name = "report_nearby_entities"
    description = (
        "Детерминированно сообщает о nearby entities из текущего observation: "
        "какие сущности рядом, есть ли рядом конкретная сущность, сколько их, "
        "есть ли рядом dropped items или vehicles."
    )
    args_schema = {
        "category": "string - one of: nearby, dropped_items, vehicles",
        "mode": "string - one of: summary, has_name, count_name, has_attitude, count_attitude",
        "target_name": "string - optional entity/item/vehicle name for has_name or count_name",
        "attitude": "string - optional one of: hostile, neutral, friendly, utility for summary/has_attitude/count_attitude",
    }

    def use(self, client: MinecraftClient, arguments: dict) -> tuple[bool, dict]:
        observation = client.observe()
        entities = observation["entities"]

        category = arguments["category"]
        mode = arguments["mode"]
        target_name = arguments.get("target_name")
        attitude = arguments.get("attitude")

        if category == "nearby":
            if mode == "summary":
                summary = entities["summary"]

                if attitude is not None:
                    summary = {}
                    for entity in entities["nearby"]:
                        if entity.get("attitude") != attitude:
                            continue
                        name = entity["name"]
                        summary[name] = summary.get(name, 0) + 1

                if not summary:
                    if attitude is not None:
                        attitude_label = ENTITY_ATTITUDE_LABELS.get(attitude, f"entities with attitude={attitude}")
                        text = f"Рядом нет {attitude_label}."
                    else:
                        text = "Рядом нет наблюдаемых сущностей."
                else:
                    parts = [f"{name}: {count}" for name, count in sorted(summary.items())]
                    if attitude is not None:
                        attitude_label = ENTITY_ATTITUDE_LABELS.get(attitude, f"entities with attitude={attitude}")
                        text = f"Рядом наблюдаются {attitude_label}: " + ", ".join(parts)
                    else:
                        text = "Рядом наблюдаются сущности: " + ", ".join(parts)

            elif mode == "has_name":
                if not target_name:
                    return False, {"error": "target_name is required for nearby/has_name"}

                count = int(entities["summary"].get(target_name, 0))
                if count > 0:
                    text = f"Да, рядом есть {target_name}."
                else:
                    text = f"Нет, рядом нет {target_name}."

            elif mode == "count_name":
                if not target_name:
                    return False, {"error": "target_name is required for nearby/count_name"}

                count = int(entities["summary"].get(target_name, 0))
                text = f"Рядом {count} сущностей {target_name}."

            elif mode == "has_attitude":
                if not attitude:
                    return False, {"error": "attitude is required for nearby/has_attitude"}

                count = int(entities["attitude_summary"].get(attitude, 0))
                attitude_label = ENTITY_ATTITUDE_LABELS.get(attitude, f"entities with attitude={attitude}")
                if count > 0:
                    text = f"Да, рядом есть {attitude_label}."
                else:
                    text = f"Нет, рядом нет {attitude_label}."

            elif mode == "count_attitude":
                if not attitude:
                    return False, {"error": "attitude is required for nearby/count_attitude"}

                count = int(entities["attitude_summary"].get(attitude, 0))
                attitude_label = ENTITY_ATTITUDE_LABELS.get(attitude, f"entities with attitude={attitude}")
                text = f"Рядом {count} {attitude_label}."

            else:
                return False, {"error": f"unknown nearby mode: {mode}"}

        elif category == "dropped_items":
            if mode == "summary":
                summary = entities["dropped_items_summary"]
                if not summary:
                    text = "Рядом на земле нет dropped items."
                else:
                    parts = [f"{name}: {count}" for name, count in sorted(summary.items())]
                    text = "Рядом на земле лежат: " + ", ".join(parts)

            elif mode == "has_name":
                if not target_name:
                    return False, {"error": "target_name is required for dropped_items/has_name"}

                count = int(entities["dropped_items_summary"].get(target_name, 0))
                if count > 0:
                    text = f"Да, рядом на земле есть {target_name}."
                else:
                    text = f"Нет, рядом на земле нет {target_name}."

            elif mode == "count_name":
                if not target_name:
                    return False, {"error": "target_name is required for dropped_items/count_name"}

                count = int(entities["dropped_items_summary"].get(target_name, 0))
                text = f"Рядом на земле {count} dropped items {target_name}."

            else:
                return False, {"error": f"unknown dropped_items mode: {mode}"}

        elif category == "vehicles":
            if mode == "summary":
                summary = entities["vehicles_summary"]
                if not summary:
                    text = "Рядом нет наблюдаемых vehicles."
                else:
                    parts = [f"{name}: {count}" for name, count in sorted(summary.items())]
                    text = "Рядом наблюдаются vehicles: " + ", ".join(parts)

            elif mode == "has_name":
                if not target_name:
                    return False, {"error": "target_name is required for vehicles/has_name"}

                count = int(entities["vehicles_summary"].get(target_name, 0))
                if count > 0:
                    text = f"Да, рядом есть {target_name}."
                else:
                    text = f"Нет, рядом нет {target_name}."

            elif mode == "count_name":
                if not target_name:
                    return False, {"error": "target_name is required for vehicles/count_name"}

                count = int(entities["vehicles_summary"].get(target_name, 0))
                text = f"Рядом {count} vehicles {target_name}."

            else:
                return False, {"error": f"unknown vehicles mode: {mode}"}

        else:
            return False, {"error": f"unknown category: {category}"}

        client.say(text)
        return True, {
            "category": category,
            "mode": mode,
            "target_name": target_name,
            "attitude": attitude,
            "text": text,
        }
