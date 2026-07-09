def object_key(obj: dict) -> tuple:
    return (
        obj["name"],
        obj["x"],
        obj["y"],
        obj["z"],
    )


def diff_observations(before: dict, after: dict) -> dict:
    before_objects = before["vision"]["nearby_objects"]
    after_objects = after["vision"]["nearby_objects"]

    before_set = {object_key(obj): obj for obj in before_objects}
    after_set = {object_key(obj): obj for obj in after_objects}

    disappeared = [
        before_set[key]
        for key in before_set.keys() - after_set.keys()
    ]

    appeared = [
        after_set[key]
        for key in after_set.keys() - before_set.keys()
    ]

    return {
        "nearby_objects_disappeared": disappeared,
        "nearby_objects_appeared": appeared,
        "block_at_cursor_before": before["vision"]["block_at_cursor"],
        "block_at_cursor_after": after["vision"]["block_at_cursor"],
    }
