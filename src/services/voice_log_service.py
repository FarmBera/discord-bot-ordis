# src/services/voice_log_service.py
from src.utils.db_helper import transaction, query_reader


class VoiceLogService:
    @staticmethod
    async def create_session(pool, user_id, user_name, display_name, channel):
        async with transaction(pool) as cursor:
            await cursor.execute(
                "INSERT INTO voice (user_id, user_name, display_name, channel, joined_at) "
                "VALUES (%s, %s, %s, %s, NOW())",
                (user_id, user_name, display_name, channel),
            )

    @staticmethod
    async def close_session(pool, user_id):
        async with transaction(pool) as cursor:
            await cursor.execute(
                "UPDATE voice "
                "SET left_at = NOW(), duration_sec = TIMESTAMPDIFF(SECOND, joined_at, NOW()) "
                "WHERE user_id = %s AND left_at IS NULL",
                (user_id,),
            )
            if cursor.rowcount == 0:
                return None

            await cursor.execute(
                "SELECT duration_sec FROM voice "
                "WHERE user_id = %s AND left_at IS NOT NULL "
                "ORDER BY id DESC LIMIT 1",
                (user_id,),
            )
            row = await cursor.fetchone()
            return row["duration_sec"] if row else None

    @staticmethod
    async def get_open_session(pool, user_id):
        async with query_reader(pool) as cursor:
            await cursor.execute(
                "SELECT * FROM voice "
                "WHERE user_id = %s AND left_at IS NULL "
                "ORDER BY id DESC LIMIT 1",
                (user_id,),
            )
            return await cursor.fetchone()

    @staticmethod
    async def update_channel(pool, user_id, new_channel):
        async with transaction(pool) as cursor:
            await cursor.execute(
                "UPDATE voice SET channel = %s "
                "WHERE user_id = %s AND left_at IS NULL",
                (new_channel, user_id),
            )
