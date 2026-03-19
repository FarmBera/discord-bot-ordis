import discord

from src.utils.db_helper import transaction, query_reader
from src.utils.times import timeNowDT

CURRENT_TOS_VERSION = "1.0"

_consent_cache: set[int] = set()


def clear_consent_cache():
    _consent_cache.clear()


async def has_consented(pool, user_id: int) -> bool:
    """
    Check user's current consent to the terms and conditions
    """
    if user_id in _consent_cache:
        return True

    async with query_reader(pool) as cursor:
        await cursor.execute(
            "SELECT 1 FROM consent WHERE user_id = %s AND tos_version = %s",
            (user_id, CURRENT_TOS_VERSION),
        )
        row = await cursor.fetchone()

    if row:
        _consent_cache.add(user_id)
        return True

    return False


async def save_consent(interact: discord.Interaction) -> None:
    """
    Store the user's consent record in the database and add it to the cache.
    If a record already exists, update the version and timestamp
    """
    pool = interact.client.db
    uid = interact.user.id

    async with transaction(pool) as cursor:
        await cursor.execute(
            """
            INSERT INTO consent (user_id, user_name, display_name, agreed_at, tos_version)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE agreed_at   = VALUES(agreed_at),
                                    tos_version = VALUES(tos_version)
            """,
            (
                uid,
                interact.user.name,
                interact.user.display_name,
                timeNowDT(),
                CURRENT_TOS_VERSION,
            ),
        )

    _consent_cache.add(uid)
