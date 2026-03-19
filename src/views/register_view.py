import discord

from config.config import LOG_TYPE
from src.translator import ts
from src.services.channel_service import ChannelService
from src.utils.logging_utils import save_log
from src.utils.return_err import return_traceback
from src.views.consent_view import check_consent
from src.views.help_view import SupportView

KEY_PARTY: str = "party_ch"
KEY_TRADE: str = "trade_ch"
KEY_COMPLAIN: str = "complain_ch"

pf: str = "cmd.register."

OPTIONS = {
    KEY_PARTY: ts.get(f"{pf}party"),
    KEY_TRADE: ts.get(f"{pf}trade"),
    KEY_COMPLAIN: ts.get(f"{pf}complain"),
}


async def fetch_channel(interact: discord.Interaction) -> dict | None:
    channel: dict = await ChannelService.getChannels(interact)

    if not channel:
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.warn,
            cmd=f"{LOG_TYPE.cmd}.register",
            interact=interact,
            msg="fetched guild & channel, but not found",
        )
        await interact.followup.send(
            content=ts.get("cmd.err-limit-server"), view=SupportView(), ephemeral=True
        )
        return None

    return channel


def parse_channel(interact: discord.Interaction, channel) -> str:
    party = channel.get("party_ch")
    trade = channel.get("trade_ch")
    complain = channel.get("complain_ch")

    none: str = ts.get(f"{pf}none")
    if party:
        party = interact.client.get_channel(party)
        party = party.name
    else:
        party = none

    if trade:
        trade = interact.client.get_channel(trade)
        trade = trade.name
    else:
        trade = none

    if complain:
        complain = interact.client.get_channel(complain)
        complain = complain.name
    else:
        complain = none

    return ts.get(f"{pf}current").format(party=party, trade=trade, complain=complain)


class ChannelSelect(discord.ui.Select):
    def __init__(self):
        options = []
        # create options
        for key, label in OPTIONS.items():
            options.append(discord.SelectOption(label=label, value=key))

        super().__init__(
            placeholder=ts.get(f"{pf}placeholder"),
            min_values=1,
            max_values=1,
            options=options,
        )

    async def on_error(
        self, interact: discord.Interaction, error: Exception, item: discord.ui.Item
    ) -> None:
        await interact.edit_original_response(
            content=ts.get(f"general.error-cmd"), embed=None, view=None
        )
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.err,
            cmd=f"{LOG_TYPE.cmd}.set-noti-insert",
            interact=interact,
            msg=f"error: {error}",
            obj=f"{self.values}\n{item}\n{return_traceback()}",
        )

    async def callback(self, interact: discord.Interaction):
        await interact.response.defer(ephemeral=True)
        # print(self.values)

        curr_channel = self.values[0].replace("'", "")
        # print(curr_channel)
        await ChannelService.setChannels(interact, curr_channel, interact.channel_id)

        channel = await fetch_channel(interact)
        output = parse_channel(interact, channel)
        await interact.edit_original_response(content=output, embed=None, view=None)
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.cmd,
            cmd=f"{LOG_TYPE.cmd}.set-noti-insert",
            interact=interact,
            msg="successfully inserted",
            obj=f"{self.values}",
        )


class RegisterView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(ChannelSelect())


async def register_cmd_helper(interact: discord.Interaction):
    await interact.response.defer(ephemeral=True)
    if not await check_consent(interact, isFollowUp=True):
        return

    ch: dict = await fetch_channel(interact)
    output: str = parse_channel(interact, ch)

    await interact.followup.send(content=output, view=RegisterView(), ephemeral=True)
    await save_log(
        pool=interact.client.db,
        type=LOG_TYPE.cmd,
        cmd=f"{LOG_TYPE.cmd}.register",
        interact=interact,
        msg="cmd used",
    )
