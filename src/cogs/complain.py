import discord
from discord import app_commands
from discord.ext import commands

from config.TOKEN import HOMEPAGE, SERVER_NAME
from config.config import LOG_TYPE
from src.constants.keys import COOLDOWN_5_MIN
from src.services.channel_service import ChannelService
from src.translator import ts
from src.utils.logging_utils import save_log
from src.views.complain_view import pf, ApplyButtonView
from src.views.consent_view import check_consent

complain_guide: discord.Embed = discord.Embed(
    description=ts.get(f"{pf}info").format(SERVER_NAME=SERVER_NAME, HOMEPAGE=HOMEPAGE),
    color=discord.Color.yellow(),
)


class ComplainCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="complain", description=f"{pf}desc")
    @discord.app_commands.checks.cooldown(
        1, COOLDOWN_5_MIN, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_receive_complain(self, interact: discord.Interaction) -> None:
        await interact.response.defer(ephemeral=True)

        if not await check_consent(interact):
            return

        # get channel
        channel_list = await ChannelService.getChannels(interact)
        if not channel_list:
            await interact.followup.send(ts.get("cmd.err-limit-server"), ephemeral=True)
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd=f"cmd.complain",
                interact=interact,
                msg="cmd used, but unauthorized server",
            )
            return

        # fetch channel
        channel_id = channel_list.get("complain_ch")
        target_channel = interact.client.get_channel(channel_id)
        if not target_channel:
            await interact.followup.send(ts.get(f"{pf}err-channel"), ephemeral=True)
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd=f"cmd.complain",
                interact=interact,
                msg="cmd used, but complain channel not found",
            )
            return

        # create view & send it
        await interact.followup.send(
            embed=complain_guide,
            view=ApplyButtonView(interact=interact),
            ephemeral=True,
        )
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.cmd,
            cmd=f"cmd.complain",
            interact=interact,
            msg="cmd used",
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(ComplainCommands(bot))
