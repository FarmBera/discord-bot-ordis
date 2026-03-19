import discord
from discord import app_commands
from discord.ext import commands

from config.config import LOG_TYPE
from src.constants.keys import COOLDOWN_CREATE
from src.services.channel_service import ChannelService
from src.services.party_service import PartyService
from src.services.queue_manager import add_job, JobType
from src.translator import ts
from src.utils.logging_utils import save_log
from src.utils.permission import is_banned_user
from src.utils.return_err import return_traceback
from src.views.consent_view import check_consent
from src.views.help_view import SupportView
from src.views.party_view import pf, MIN_SIZE, MAX_SIZE


class PartyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="party", description="cmd.party.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_CREATE, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.describe(
        title="cmd.party.desc-title",
        game_name="cmd.party.desc-game-name",
        departure="cmd.party.desc-departure",
        descriptions="cmd.party.desc-descriptions",
        number_of_user="cmd.party.desc-number-of-user",
    )
    async def cmd_create_party(
        self,
        interact: discord.Interaction,
        title: str,
        game_name: str,
        departure: str = None,
        descriptions: str = ts.get(f"{pf}c-no-desc"),
        number_of_user: int = 4,
    ):
        await interact.response.defer(ephemeral=True)
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.cmd,
            cmd=f"cmd.party.create",
            interact=interact,
            msg="cmd used",  # VAR
            obj=f"T:{title}\nTYPE:{game_name}\nDEPT:{departure}\nDESC:{descriptions}\n{number_of_user}",
        )
        if await is_banned_user(interact, isFollowUp=True):
            return
        if not await check_consent(interact, isFollowUp=True):
            return

        # get channel
        channel_list = await ChannelService.getChannels(interact)
        if not channel_list:
            await interact.followup.send(ts.get("cmd.err-limit-server"), ephemeral=True)
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd=f"cmd.party",
                interact=interact,
                msg="cmd used, but unregistered server",
            )
            return

        # fetch
        target_channel = self.bot.get_channel(channel_list.get("party_ch"))
        if not target_channel:
            await interact.followup.send(ts.get(f"cmd.ch-not-found"), ephemeral=True)
            return

        if number_of_user < MIN_SIZE:
            await interact.followup.send(
                ts.get(f"{pf}pt-low").format(num=MIN_SIZE), ephemeral=True
            )
            number_of_user = 4

        elif number_of_user > MAX_SIZE:
            await interact.followup.send(
                ts.get(f"{pf}pt-high").format(num=MAX_SIZE), ephemeral=True
            )
            number_of_user = MAX_SIZE

        # create party & insert into db
        try:
            party_id = await PartyService.create_party(
                self.bot.db,
                interact.user.id,
                interact.user.display_name,
                interact.user.mention,
                title,
                game_name,
                departure,
                number_of_user,
                descriptions,
            )
        except Exception as e:
            await interact.followup.send(
                ts.get("cmd.err-db"), view=SupportView(), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd=f"cmd.party",
                interact=interact,
                msg="cmd used, but DB ERR",  # VAR
                obj=f"{e}\nT:{title}\nTYPE:{game_name}\nDEPT:{departure}\nDESC:{descriptions}\nNOU:{number_of_user}\n{return_traceback()}",
            )
            return

        data = {
            "id": party_id,
            "host_id": interact.user.id,
            "host_mention": interact.user.mention,
            "title": title,
            "mission": game_name,
            "departure": departure,
            "max_users": number_of_user,
            "participants": [interact.user.mention],
            "is_closed": False,
            "description": descriptions,
        }
        await add_job(
            JobType.PARTY_CREATE,
            {"interact": interact, "data": data, "target_channel": target_channel},
        )
        await interact.followup.send(
            f"✅ '{target_channel.mention}' {ts.get(f'{pf}pt-create')}", ephemeral=True
        )
        await self.bot.trigger_queue_processing()


async def setup(bot: commands.Bot):
    await bot.add_cog(PartyCog(bot))
