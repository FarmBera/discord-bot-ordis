import datetime as dt

import discord
from discord import ui
from discord.ext import commands

from config.config import LOG_TYPE
from src.constants.keys import (
    COOLDOWN_ACTION,
    COOLDOWN_SHORT,
    COOLDOWN_BTN_CALL,
)
from src.translator import ts
from src.utils.db_helper import query_reader
from src.utils.logging_utils import save_log
from src.utils.times import convert_remain


async def cmd_helper_maintenance(interact: discord.Interaction, arg: str = "") -> None:
    async with query_reader(interact.client.db) as cursor:
        # delta time
        await cursor.execute("SELECT value FROM vari WHERE name='delta_time'")
        delta_time = await cursor.fetchone()
        delta_time = int(delta_time["value"])

        # get started time
        await cursor.execute("SELECT updated_at FROM vari WHERE name='start_time'")
        start_time = await cursor.fetchone()
        start_time = start_time["updated_at"]

    # calculate time
    time_target = start_time + dt.timedelta(minutes=delta_time)

    txt = ts.get("maintenance.content").format(
        remain=convert_remain(time_target.timestamp())
    )

    # send message
    await interact.response.send_message(
        embed=discord.Embed(description=txt, color=0xFF0000),  # VAR: color
        ephemeral=True,
    )
    await save_log(
        pool=interact.client.db,
        type=f"{LOG_TYPE.cmd}.{LOG_TYPE.maintenance}",
        cmd=f"cmd.{ts.get(f'cmd.help.cmd')}",
        interact=interact,
        msg=f"cmd used in maintenance mode: {arg}",
    )


EVENT_TYPE: str = f"{LOG_TYPE.event}.{LOG_TYPE.maintenance}"
EVENT_COOLDOWN: str = LOG_TYPE.cooldown


pf: str = "cmd.party."
pf_edit: str = f"{pf}p-edit-modal-"
pf_size: str = f"{pf}p-size-modal-"
pf_btn: str = f"{pf}p-del-modal-"
pf_pv: str = f"{pf}pv-"


class PartyView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # make the button persistent
        self.cooldown_action = commands.CooldownMapping.from_cooldown(
            1, COOLDOWN_ACTION, commands.BucketType.user
        )
        self.cooldown_manage = commands.CooldownMapping.from_cooldown(
            1, COOLDOWN_SHORT, commands.BucketType.user
        )
        self.cooldown_call = commands.CooldownMapping.from_cooldown(
            1, COOLDOWN_BTN_CALL, commands.BucketType.user
        )

    @ui.button(
        label=ts.get(f"{pf}pv-join-btn"),
        style=discord.ButtonStyle.success,
        custom_id="party_join",
        row=1,
    )
    async def join_party(
        self, interact: discord.Interaction, button: discord.ui.Button
    ):
        cmd = "PartyView.btn.join"
        await cmd_helper_maintenance(interact)
        await save_log(
            pool=interact.client.db,
            type=EVENT_TYPE,
            cmd=cmd,
            interact=interact,
            msg=f"PartyView -> join_party",
        )

    @ui.button(
        label=ts.get(f"{pf}pv-leave-btn"),
        style=discord.ButtonStyle.danger,
        custom_id="party_leave",
        row=1,
    )
    async def leave_party(
        self, interact: discord.Interaction, button: discord.ui.Button
    ):
        cmd = "PartyView.btn.leave"
        await cmd_helper_maintenance(interact)
        await save_log(
            pool=interact.client.db,
            type=EVENT_TYPE,
            cmd=cmd,
            interact=interact,
            msg=f"PartyView -> leave_party",
        )

    @ui.button(
        label=ts.get(f"{pf}pv-mod-all"),
        style=discord.ButtonStyle.secondary,
        custom_id="party_edit_info",
        row=1,
    )
    async def edit_info(self, interact: discord.Interaction, button: ui.Button):
        cmd = "PartyView.btn.edit-info"
        await cmd_helper_maintenance(interact)
        await save_log(
            pool=interact.client.db,
            type=EVENT_TYPE,
            cmd=cmd,
            interact=interact,
            msg=f"PartyView -> edit_info",
        )

    @ui.button(
        label=ts.get(f"{pf}pv-done"),
        style=discord.ButtonStyle.primary,
        custom_id="party_toggle_close",
        row=2,
    )
    async def toggle_close(self, interact: discord.Interaction, button: ui.Button):
        cmd = "PartyView.btn.togle-close"
        await cmd_helper_maintenance(interact)
        await save_log(
            pool=interact.client.db,
            type=EVENT_TYPE,
            cmd=cmd,
            interact=interact,
            msg=f"PartyView -> toggle_close",
        )

    @ui.button(
        label=ts.get(f"{pf}pv-call-label"),
        style=discord.ButtonStyle.secondary,
        custom_id="party_call_members",
        row=2,
    )
    async def call_members(self, interact: discord.Interaction, button: ui.Button):
        cmd = "PartyView.btn.member-call"
        await cmd_helper_maintenance(interact)
        await save_log(
            pool=interact.client.db,
            type=EVENT_TYPE,
            cmd=cmd,
            interact=interact,
            msg=f"PartyView -> call_members",
        )

    @ui.button(
        label=ts.get(f"{pf}pv-kick-label"),
        style=discord.ButtonStyle.secondary,
        custom_id="party_kick_member",
        row=2,
    )
    async def kick_member(self, interact: discord.Interaction, button: ui.Button):
        cmd = "PartyView.btn.member-kick"
        await cmd_helper_maintenance(interact)
        await save_log(
            pool=interact.client.db,
            type=EVENT_TYPE,
            cmd=cmd,
            interact=interact,
            msg=f"PartyView -> kick_member",
        )

    @ui.button(
        label=ts.get(f"{pf}pv-del-label"),
        style=discord.ButtonStyle.danger,
        custom_id="party_delete",
        row=2,
    )
    async def delete_party(self, interact: discord.Interaction, button: ui.Button):
        cmd = "PartyView.btn.delete-party"
        await cmd_helper_maintenance(interact)
        await save_log(
            pool=interact.client.db,
            type=EVENT_TYPE,
            cmd=cmd,
            interact=interact,
            msg=f"PartyView -> delete_party",
        )


pf: str = "cmd.trade."


class TradeView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldown_manage = commands.CooldownMapping.from_cooldown(
            1, COOLDOWN_SHORT, commands.BucketType.user
        )
        self.cooldown_call = commands.CooldownMapping.from_cooldown(
            1, COOLDOWN_BTN_CALL, commands.BucketType.user
        )

    @ui.button(
        label=ts.get(f"{pf}btn-trade"),
        style=discord.ButtonStyle.primary,
        custom_id="trade_btn_trade",
    )
    async def trade_action(self, interact: discord.Interaction, button: ui.Button):
        cmd: str = "TradeView -> trade_action"
        await cmd_helper_maintenance(interact)
        await save_log(
            pool=interact.client.db,
            type=EVENT_TYPE,
            cmd=cmd,
            interact=interact,
            msg=cmd,
        )

    @ui.button(
        label=ts.get(f"{pf}btn-edit-info"),
        style=discord.ButtonStyle.secondary,
        custom_id="trade_btn_edit_info",
    )
    async def edit_trade_info(self, interact: discord.Interaction, button: ui.Button):
        cmd: str = "TradeView -> edit_trade_info"
        await cmd_helper_maintenance(interact)
        await save_log(
            pool=interact.client.db,
            type=EVENT_TYPE,
            cmd=cmd,
            interact=interact,
            msg=cmd,
        )

    @ui.button(
        label=ts.get(f"{pf}btn-edit-nickname"),
        style=discord.ButtonStyle.secondary,
        custom_id="trade_btn_edit_nick",
    )
    async def edit_nickname(self, interact: discord.Interaction, button: ui.Button):
        cmd = "TradeView -> edit_nickname"
        await cmd_helper_maintenance(interact)
        await save_log(
            pool=interact.client.db,
            type=EVENT_TYPE,
            cmd=cmd,
            interact=interact,
            msg=cmd,
        )

    @ui.button(
        label=ts.get(f"{pf}btn-close"),
        style=discord.ButtonStyle.danger,
        custom_id="trade_btn_edit_close",
    )
    async def close_trade(self, interact: discord.Interaction, button: ui.Button):
        cmd = "TradeView -> close_trade"
        await cmd_helper_maintenance(interact)
        await save_log(
            pool=interact.client.db,
            type=EVENT_TYPE,
            cmd=cmd,
            interact=interact,
            msg=cmd,
        )
