from enum import Enum, auto


class JobType(Enum):
    # party
    PARTY_CREATE = auto()
    PARTY_UPDATE = auto()
    PARTY_DELETE = auto()
    PARTY_TOGGLE = auto()
    # trade
    TRADE_CREATE = auto()
    TRADE_UPDATE = auto()
    TRADE_DELETE = auto()


GLOBAL_QUEUE = []


async def add_job(job_type: JobType, data: dict) -> None:
    """Add task into integrated queue"""
    global GLOBAL_QUEUE

    # duplicate protection
    if job_type in [
        JobType.PARTY_UPDATE,
        JobType.TRADE_UPDATE,
        JobType.PARTY_DELETE,
        JobType.TRADE_DELETE,
    ]:
        try:
            target_id = (
                data.get("interact").message.id
                if data.get("interact")
                else data.get("origin_msg").id
            )

            def is_same_task(item):
                if item["type"] != job_type:
                    return False
                item_data = item["data"]
                item_id = (
                    item_data.get("interact").message.id
                    if item_data.get("interact")
                    else item_data.get("origin_msg").id
                )
                return item_id == target_id

            GLOBAL_QUEUE[:] = [item for item in GLOBAL_QUEUE if not is_same_task(item)]
        except:
            pass

    GLOBAL_QUEUE.append({"type": job_type, "data": data})


def get_queue_status() -> int:
    global GLOBAL_QUEUE
    return len(GLOBAL_QUEUE)
