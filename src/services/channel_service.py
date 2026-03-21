import discord

from src.utils.db_helper import query_reader, transaction
from src.utils.file_io import yaml_open

CHANNELS = yaml_open("config/channel")


class ChannelService:
    @staticmethod
    async def getChannels(interact: discord.Interaction = None) -> dict | None:
        return CHANNELS

        pool = interact.client.db
        guild_id = interact.guild_id

        async with query_reader(pool) as cursor:
            await cursor.execute(
                "SELECT guild_id,party_ch,trade_ch,complain_ch,warn_log_ch,is_allowed FROM channels WHERE guild_id = %s LIMIT 1",
                (guild_id,),
            )
            channels = await cursor.fetchone()

        if not channels:
            return None

        fetched_id = channels.get("guild_id")

        if not fetched_id or fetched_id != guild_id or not channels.get("is_allowed"):
            return None

        return channels

    @staticmethod
    async def setChannels(
        interact: discord.Interaction, channel: str, this_channel: int
    ) -> None:
        pool = interact.client.db
        guild_id = interact.guild_id

        async with transaction(pool) as cur:
            await cur.execute(
                f"UPDATE channels SET {channel}=%s WHERE guild_id=%s",
                (this_channel, guild_id),
            )
