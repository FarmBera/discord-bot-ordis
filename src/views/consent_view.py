import discord
from discord import ui

from config.TOKEN import HOMEPAGE
from config.config import LOG_TYPE
from src.services.consent_service import CURRENT_TOS_VERSION, save_consent
from src.services.consent_service import has_consented
from src.translator import ts
from src.utils.logging_utils import save_log
from src.utils.return_err import return_traceback
from src.views.help_view import SupportView

pf = "cmd.consent."


class ConsentView(ui.View):
    def __init__(self, interact: discord.Interaction):
        super().__init__(timeout=300)
        self.interact = interact

    @staticmethod
    def build_notice_embed() -> discord.Embed:
        embed = discord.Embed(
            description=ts.get(f"{pf}notice").format(HOMEPAGE=HOMEPAGE),
            color=discord.Color.blurple(),
        )
        embed.set_footer(text=ts.get(f"{pf}version").format(ver=CURRENT_TOS_VERSION))
        return embed

    async def on_timeout(self):
        cmd = "ConsentView.timeout"
        try:
            await self.interact.edit_original_response(
                content=ts.get("cmd.err-timeout"),
                embed=None,
                view=None,
            )
            await save_log(
                pool=self.interact.client.db,
                type=LOG_TYPE.event,
                cmd=cmd,
                interact=self.interact,
                msg="ConsentView -> timeout",
            )
        except discord.NotFound:
            await save_log(
                pool=self.interact.client.db,
                type=LOG_TYPE.info,
                cmd=cmd,
                interact=self.interact,
                msg="ConsentView -> timeout, but Not Found",
            )
        except Exception:
            await save_log(
                pool=self.interact.client.db,
                type=LOG_TYPE.err,
                cmd=cmd,
                interact=self.interact,
                msg="ConsentView -> timeout, but ERR",
                obj=return_traceback(),
            )

    @ui.button(
        label=ts.get(f"{pf}btn-agree"),
        style=discord.ButtonStyle.success,
    )
    async def agree_button(self, interact: discord.Interaction, button: ui.Button):
        cmd = "ConsentView.btn.agree"
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd=cmd,
            interact=interact,
            msg="ConsentView -> agree_button clicked",
        )

        if interact.user.id != self.interact.user.id:
            await interact.response.send_message(
                ts.get(f"{pf}err-not-owner"), ephemeral=True
            )
            return

        try:
            await save_consent(interact)

            await interact.response.edit_message(
                content=ts.get(f"{pf}agreed"),
                embed=None,
                view=None,
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.event,
                cmd=cmd,
                interact=interact,
                msg=f"ConsentConfirmView -> user agreed (v{CURRENT_TOS_VERSION})",
            )
        except Exception:
            await interact.response.edit_message(
                content=ts.get(f"{pf}err-save"),
                embed=None,
                view=SupportView(),
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd=cmd,
                interact=interact,
                msg="ConsentConfirmView -> confirm, but ERR",
                obj=return_traceback(),
            )
        self.stop()

    @ui.button(
        label=ts.get(f"{pf}btn-disagree"),
        style=discord.ButtonStyle.danger,
    )
    async def disagree_button(self, interact: discord.Interaction, button: ui.Button):
        cmd = "ConsentView.btn.disagree"

        if interact.user.id != self.interact.user.id:
            await interact.response.send_message(
                ts.get(f"{pf}err-not-owner"), ephemeral=True
            )
            return

        await interact.response.edit_message(
            content=ts.get(f"{pf}cancelled"),
            embed=None,
            view=None,
        )
        self.stop()
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd=cmd,
            interact=interact,
            msg="ConsentConfirmView -> cancel clicked",
        )


async def check_consent(
    interact: discord.Interaction, isFollowUp: bool = False
) -> bool:
    """
    used when an interaction occurs to verify whether the user has agreed to the terms and conditions.
    """
    if await has_consented(interact.client.db, interact.user.id):
        return True

    embed = ConsentView.build_notice_embed()
    view = ConsentView(interact)
    if isFollowUp:
        await interact.followup.send(embed=embed, view=view, ephemeral=True)
    else:
        await interact.response.send_message(embed=embed, view=view, ephemeral=True)
    await save_log(
        pool=interact.client.db,
        type=LOG_TYPE.info,
        cmd="first-use",
        interact=interact,
        msg="Used bot for the first time!",
    )
    return False
