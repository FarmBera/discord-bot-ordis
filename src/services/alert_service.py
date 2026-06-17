from config.config import LOG_TYPE
from src.constants.notification import DB_COLUMN_MAP, NOTI_LABELS
from src.utils.db_helper import transaction
from src.utils.logging_utils import save_log
from src.utils.return_err import return_traceback


async def fetch_current_subscriptions(db, channel_id: int) -> list:
    """
    get the current list of notifications subscribed to interacted channel from the db.
    """
    active_labels = []
    cols = list(DB_COLUMN_MAP.values())
    # column name mapping
    col_to_key = {v: k for k, v in DB_COLUMN_MAP.items()}

    query = f"SELECT {', '.join(cols)} FROM webhooks WHERE channel_id = %s"
    try:
        async with transaction(db) as cursor:
            await cursor.execute(query, (channel_id,))
            row = await cursor.fetchone()

        if row:
            for col_name in cols:
                val = row[col_name]

                if val == 1:
                    key = col_to_key.get(col_name)
                    # convert labels
                    if key and key in NOTI_LABELS:
                        active_labels.append(NOTI_LABELS[key])
    except Exception as e:
        await save_log(
            pool=db,
            type=LOG_TYPE.cmd,
            cmd="fetch_current_subscriptions",
            msg="db select error",  # VAR
            obj=return_traceback(),
        )
        print(f"[Error] fetch_current_subscriptions: {e}")

    return active_labels
