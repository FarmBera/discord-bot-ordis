# PRIVATE FUNC
def extractID(obj_prev, obj_new):
    return (
        {item["_id"]["$oid"] for item in obj_prev},
        {item["_id"]["$oid"] for item in obj_new},
    )


def checkMissingIds(obj_prev, obj_new):
    should_save_data: bool = False

    prev_ids, new_ids = extractID(obj_prev, obj_new)

    if prev_ids != new_ids:
        should_save_data = True

    # check newly added items
    newly_added_ids = new_ids - prev_ids
    return should_save_data, newly_added_ids


def checkMissingItem(obj_new, newly_added_ids):
    return [item for item in obj_new if item["_id"]["$oid"] in newly_added_ids]


def checkExpiredItem(obj_prev, obj_new):
    prev_ids, new_ids = extractID(obj_prev, obj_new)
    return prev_ids != new_ids
