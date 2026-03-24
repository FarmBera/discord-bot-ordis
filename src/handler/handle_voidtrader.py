from src.parser.voidTraders import isBaroActive


def _extract_timestamp(value) -> int:
    if isinstance(value, dict) and "$date" in value:
        date_val = value["$date"]
        if isinstance(date_val, dict) and "$numberLong" in date_val:
            return int(date_val["$numberLong"])
        return int(date_val)
    return int(value)


def handleVoidTrader(prev, new):
    prev_data: dict = prev[-1] if isinstance(prev, list) and prev else prev
    new_data: dict = new[-1] if isinstance(new, list) and new else new
    events: list = []

    prev_act = _extract_timestamp(prev_data.get("Activation"))
    new_act = _extract_timestamp(new_data.get("Activation"))
    new_exp = _extract_timestamp(new_data.get("Expiry"))

    # 1. is new baro scheduled (check new baro)
    if prev_act != new_act:
        events.append(
            {
                "text_key": "cmd.void-traders.baro-new",
                "embed_color": 0xFFDD00,
                "have_custom_msg": False,
            }
        )

    # 2. check baro just became active
    prev_active = getattr(handleVoidTrader, "_was_active", False)
    curr_active = isBaroActive(new_act, new_exp)

    if not prev_active and curr_active:
        events.append(
            {
                "text_key": "cmd.void-traders.baro-appear",
                "embed_color": None,
                "have_custom_msg": True,
            }
        )

    handleVoidTrader._was_active = curr_active

    return events
