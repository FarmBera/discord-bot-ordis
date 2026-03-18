# cogs/voice_log.py

import discord
from discord.ext import commands

from src.constants.color import C
from src.services.channel_service import ChannelService
from src.services.voice_log_service import VoiceLogService
from src.utils.times import timeNowDT


class ACT:
    quit = "🔇 퇴장"
    enter = "🎙️ 입장"
    move = "↔️ 이동"


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)

    parts = []
    if hours:
        parts.append(f"{hours}시간")
    if minutes:
        parts.append(f"{minutes}분")
    parts.append(f"{secs}초")
    return " ".join(parts)


class VoiceLog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.LOG_CHANNEL_ID = None

    @commands.Cog.listener()
    async def on_ready(self):
        if self.LOG_CHANNEL_ID is not None:
            return

        self.LOG_CHANNEL_ID = await ChannelService.getChannels()
        if self.LOG_CHANNEL_ID:
            self.LOG_CHANNEL_ID = self.LOG_CHANNEL_ID["voice_log_ch"]
        else:
            print(C.red, "ERROR: Unable to get voice_log_ch", C.default, sep="")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        log_channel = self.bot.get_channel(self.LOG_CHANNEL_ID)
        if not log_channel:
            return

        timestamp = timeNowDT().strftime("%Y-%m-%d %H:%M:%S")
        pool = self.bot.db

        # quit voice channel
        if before.channel is not None and after.channel is None:
            action, color, channel_name = (
                ACT.quit,
                discord.Color.orange(),
                before.channel.name,
            )
        # entrance voice channel
        elif before.channel is None and after.channel is not None:
            await VoiceLogService.create_session(
                pool, member.id, member.name, member.display_name, after.channel.name
            )
            action, color, channel_name = (
                ACT.enter,
                discord.Color.green(),
                after.channel.name,
            )
        # move to another voice channel
        elif before.channel != after.channel:
            await VoiceLogService.update_channel(pool, member.id, after.channel.name)
            action, color, channel_name = (
                ACT.move,
                discord.Color.blue(),
                f"{before.channel.name} --> {after.channel.name}",
            )
        else:
            return

        embed = discord.Embed(title=f"음성 채널 {action}", color=color)
        embed.add_field(name="멤버", value=member.mention, inline=True)
        embed.add_field(name="채널", value=channel_name, inline=True)

        if action == ACT.quit:
            duration_sec = await VoiceLogService.close_session(pool, member.id)
            if duration_sec is not None:
                embed.add_field(
                    name="통화 시간",
                    value=format_duration(duration_sec),
                    inline=False,
                )

        if action == ACT.move:
            return

        embed.set_footer(text=timestamp)
        embed.set_thumbnail(url=member.display_avatar.url)

        await log_channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceLog(bot))
