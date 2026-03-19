import discord
from discord import app_commands
from discord.ext import commands

from config.config import LOG_TYPE
from src.constants.keys import COOLDOWN_DEFAULT
from src.translator import ts
from src.utils.db_helper import query_reader
from src.utils.logging_utils import save_log
from src.utils.permission import is_admin_user
from src.utils.return_err import return_traceback
from src.views.consent_view import check_consent
from src.views.help_view import SupportView
from src.views.user_warn_view import pf, WarnInputModal


class UserWarnCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # warn or ban user
    @app_commands.command(name="user-ban", description="cmd.user-ban.desc")
    @discord.app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_user_warn(
        self,
        interact: discord.Interaction,
        user: discord.Member,
    ) -> None:
        if user.id == interact.client.user.id:
            await interact.response.send_message(
                ts.get("cmd.user-ban.self-unable"), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.info,
                cmd=pf,
                interact=interact,
                msg="cannot ban myself",  # VAR
                obj=f"{user.id}\n{user.name}\n{user.global_name}\n{user.display_name}",
            )
            return

        if not await is_admin_user(
            interact, cmd=f"{LOG_TYPE.cmd}.user-ban", notify=True
        ):
            return
        if not await check_consent(interact):
            return

        try:
            async with query_reader(interact.client.db) as cursor:
                # check is already banned user
                check_ban_sql = (
                    "SELECT 1 FROM warnings WHERE user_id = %s AND banned = 1 LIMIT 1"
                )
                await cursor.execute(check_ban_sql, (user.id,))
                is_already_banned = await cursor.fetchone()

            if is_already_banned:
                await interact.followup.send(
                    ts.get(f"{pf}already-ban").format(user=user.display_name),
                    ephemeral=True,
                )
                await save_log(
                    pool=interact.client.db,
                    type=LOG_TYPE.info,
                    cmd=pf,
                    interact=interact,
                    msg="Already banned user",  # VAR
                    obj=f"{user.id}\n{user.name}\n{user.global_name}\n{user.display_name}",
                )
                # return

            modal = WarnInputModal(pool=interact.client.db, target_member=user)
            await interact.response.send_modal(modal)

            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.info,
                cmd=pf,
                interact=interact,
                msg="cmd used",  # VAR
                obj=f"{user.id}\n{user.name}\n{user.global_name}\n{user.display_name}",
            )
        except Exception as e:
            if not interact.response.is_done():
                await interact.response.send_message(
                    ts.get(f"general.error-cmd"), view=SupportView(), ephemeral=True
                )
                await save_log(
                    pool=interact.client.db,
                    type=LOG_TYPE.err,
                    cmd=pf,
                    interact=interact,
                    msg=f"cmd used, but ERR: {e}",  # VAR
                    obj=return_traceback(),
                )


async def setup(bot: commands.Bot):
    await bot.add_cog(UserWarnCommands(bot))
