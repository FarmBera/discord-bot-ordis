import discord
from discord import ui
from discord.ext import commands

from config.TOKEN import base_url_market_image
from config.config import LOG_TYPE
from src.constants.keys import COOLDOWN_SHORT, COOLDOWN_BTN_CALL
from src.parser.marketsearch import get_slug_data, create_market_url
from src.services.queue_manager import add_job, JobType
from src.services.trade_service import TradeService
from src.translator import ts
from src.utils.logging_utils import save_log
from src.utils.permission import (
    is_cooldown,
    is_admin_user,
    is_banned_user,
)
from src.utils.return_err import return_traceback
from src.views.consent_view import check_consent
from src.views.help_view import SupportView

pf = "cmd.trade."


# ----------------- Helpers -----------------
def parseNickname(nickname: str) -> str:
    return nickname.split("]")[-1].strip()


def revTradeType(trade_type: str) -> str:
    return (
        ts.get("cmd.trade.type-buy")
        if trade_type == ts.get(f"cmd.trade.type-sell")
        else ts.get(f"cmd.trade.type-sell")
    )


async def isTradeExists(interact: discord.Interaction, trade, cmd: str = "") -> bool:
    if trade:
        return True

    await interact.response.send_message(
        embed=discord.Embed(
            description=ts.get(f"{pf}err-not-found"), color=discord.Color.red()
        ),
        ephemeral=True,
    )
    await save_log(
        pool=interact.client.db,
        type=LOG_TYPE.err,
        cmd="btn",
        msg="trade not found from db",
        interact=interact,
    )
    return False


async def build_trade_embed(
    data: dict, db_pool, isDelete: bool = False, isRank: bool = False
) -> discord.Embed:
    flag, _, __, img_url = get_slug_data(data["item_name"])
    description: str = ""

    # description += await WarnService.generateWarnMsg(db_pool,data['host_id'])

    description += f"### [{data['trade_type']}] {data['item_name']}"

    if isRank and data.get("item_rank") != -1:
        description += f" ({ts.get(f'{pf}rank-simple').format(rank=data['item_rank'])})"

    description += f"""
- **{ts.get(f'{pf}creator')}:** {data['host_mention']}
- **{ts.get(f'{pf}item-name')}:** {create_market_url(data['item_name'])}
- **{ts.get(f'{pf}price-per')}:** `{data['price']:,} {ts.get(f'{pf}platinum')}` (총합 {data['price'] * data['quantity']:,} 플레)
- **{ts.get(f'{pf}quantity')}:** `{data['quantity']:,}` 개
"""
    rank_val = int(data.get("item_rank", -1))
    rank_str = f" ({rank_val} {ts.get(f'{pf}rank-label')})" if rank_val > -1 else ""

    # whispers
    if not isDelete:
        description += ts.get(f"{pf}whispers").format(
            nickname=data["game_nickname"],
            item=data["item_name"] + rank_str,
            price=data["price"],
            type=revTradeType(data["trade_type"]),
        )
    if isDelete:
        description = f"~~{description.strip().replace('~~', '')}~~"

    # embed color
    color = 0x00FF00 if not isDelete else 0xFF0000
    # generate embed
    embed = discord.Embed(description=description.strip(), color=color)
    embed.set_footer(text=f"ID: {data['id']}")
    if flag and img_url:
        embed.set_thumbnail(url=f"{base_url_market_image}{img_url}")
    return embed


async def build_trade_embed_from_db(
    message_id: int, db_pool, isDelete: bool = False
) -> discord.Embed:
    trade_data = await TradeService.get_trade_by_message_id(db_pool, message_id)
    if not trade_data:
        return discord.Embed(
            title=ts.get(f"{pf}err"),
            description=ts.get(f"{pf}err-not-found"),
            color=discord.Color.dark_red(),
        )

    return await build_trade_embed(
        {
            "id": trade_data["id"],
            "host_id": trade_data["host_id"],
            "host_mention": f"<@{trade_data['host_id']}>",
            "game_nickname": trade_data["game_nickname"],
            "trade_type": trade_data["trade_type"],
            "item_name": trade_data["item_name"],
            "item_rank": trade_data["item_rank"],
            "quantity": trade_data["quantity"],
            "price": trade_data["price"],
        },
        db_pool,
        isDelete=isDelete,
        isRank=(trade_data["item_rank"] > -1),
        # isRank=(trade_data["item_rank"] is not None),
    )


# ----------------- Modals -----------------
class EditNicknameModal(ui.Modal, title=ts.get(f"{pf}edit-nick-title")):
    def __init__(self, curr_nickname: str, interact: discord.Interaction, db_pool):
        super().__init__(timeout=None)
        self.db_pool = db_pool
        self.original_message = interact.message
        self.input_nickname = ui.TextInput(
            label=ts.get(f"{pf}edit-nick-label"), default=curr_nickname, required=True
        )
        self.add_item(self.input_nickname)

    async def on_submit(self, interact: discord.Interaction):
        try:
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.event,
                cmd="btn.edit.nickname",
                interact=interact,
                msg="EditNicknameModal -> Submit",
            )
            await TradeService.update_nickname(
                self.db_pool, interact.message.id, self.input_nickname.value
            )
            await add_job(JobType.TRADE_UPDATE, {"origin_msg": self.original_message})
            await interact.client.trigger_queue_processing()
            await interact.response.send_message(
                ts.get(f"{pf}edit-requested"), ephemeral=True
            )
        except Exception:
            await interact.response.send_message(
                ts.get(f"{pf}err-edit"), view=SupportView(), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd="btn.edit.nickname",
                interact=interact,
                msg=f"EditNicknameModal -> Submit, but ERR",
                obj=f"T:{self.input_nickname.value}\n{return_traceback()}",
            )


class EditTradeModal(ui.Modal, title=ts.get(f"{pf}edit-trade-title")):
    def __init__(self, trade_data: dict, interact: discord.Interaction, db_pool):
        super().__init__(timeout=None)
        self.db_pool = db_pool
        self.original_message = interact.message

        self.current_quantity = int(trade_data["quantity"])
        self.current_price = int(trade_data["price"])
        self.current_rank = int(trade_data.get("item_rank", -1))
        # Rank field is only rendered for rank-capable items (rank > -1)
        self.has_rank = self.current_rank > -1

        self.quantity_input = ui.TextInput(
            label=ts.get(f"{pf}edit-qty-label"),
            default=str(self.current_quantity),
            required=True,
        )
        self.add_item(self.quantity_input)

        self.price_input = ui.TextInput(
            label=ts.get(f"{pf}edit-price-label"),
            default=str(self.current_price),
            required=True,
        )
        self.add_item(self.price_input)

        self.rank_input: ui.TextInput | None = None
        if self.has_rank:
            self.rank_input = ui.TextInput(
                label=ts.get(f"{pf}edit-rank-label"),
                default=str(self.current_rank),
                required=True,
                max_length=2,
                placeholder="0",
            )
            self.add_item(self.rank_input)

    async def on_submit(self, interact: discord.Interaction):
        qty_str = self.quantity_input.value.strip()
        price_str = self.price_input.value.strip()
        rank_str = self.rank_input.value.strip() if self.rank_input else None

        # Validate all fields, collect errors together
        errors: list[str] = []
        new_quantity: int | None = None
        new_price: int | None = None
        new_rank: int | None = None

        # quantity
        if not qty_str.isdigit():
            errors.append(
                f"- {ts.get(f'{pf}edit-qty-label')}: {ts.get(f'{pf}err-invalid-value')}"
            )
        else:
            parsed_qty = int(qty_str)
            if parsed_qty < 1:
                errors.append(
                    f"- {ts.get(f'{pf}edit-qty-label')}: {ts.get(f'{pf}err-size-low')}"
                )
            else:
                new_quantity = parsed_qty

        # price
        if not price_str.isdigit() or int(price_str) < 0:
            errors.append(
                f"- {ts.get(f'{pf}edit-price-label')}: {ts.get(f'{pf}err-invalid-value')}"
            )
        else:
            new_price = int(price_str)

        # rank (optional)
        if rank_str is not None:
            if not rank_str.isdigit() or int(rank_str) < 0:
                errors.append(
                    f"- {ts.get(f'{pf}edit-rank-label')}: {ts.get(f'{pf}err-invalid-value')}"
                )
            else:
                new_rank = int(rank_str)

        if errors:
            await interact.response.send_message("\n".join(errors), ephemeral=True)
            return

        # send only changed value
        diff_kwargs: dict = {}
        change_log: list[str] = []

        if new_quantity is not None and new_quantity != self.current_quantity:
            diff_kwargs["quantity"] = new_quantity
            change_log.append(f"qty:{self.current_quantity}->{new_quantity}")
        if new_price is not None and new_price != self.current_price:
            diff_kwargs["price"] = new_price
            change_log.append(f"price:{self.current_price}->{new_price}")
        if self.has_rank and new_rank is not None and new_rank != self.current_rank:
            diff_kwargs["item_rank"] = new_rank
            change_log.append(f"rank:{self.current_rank}->{new_rank}")

        if not diff_kwargs:
            await interact.response.send_message(
                ts.get(f"{pf}edit-no-change"), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.event,
                cmd="btn.edit.trade",
                interact=interact,
                msg="EditTradeModal -> Submit, no change",
            )
            return

        try:
            await TradeService.update_trade_info(
                self.db_pool, interact.message.id, **diff_kwargs
            )
            await add_job(JobType.TRADE_UPDATE, {"origin_msg": self.original_message})
            await interact.client.trigger_queue_processing()
            await interact.response.send_message(
                ts.get(f"{pf}edit-requested"), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.event,
                cmd="btn.edit.trade",
                interact=interact,
                msg=f"EditTradeModal -> Submit {', '.join(change_log)}",
            )
        except Exception:
            await interact.response.send_message(
                ts.get(f"{pf}err-edit"), view=SupportView(), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd="btn.edit.trade",
                interact=interact,
                msg="EditTradeModal -> Submit, but ERR",
                obj=f"qty={qty_str}, price={price_str}, rank={rank_str}\n{return_traceback()}",
            )


# ----------------- Views -----------------
class ConfirmDeleteView(ui.View):
    def __init__(
        self,
        interact: discord.Interaction,
        origin_message: discord.Message,
        trade_data,
        trade_view,
    ):
        super().__init__(timeout=20)
        self.interact = interact
        self.origin_message = origin_message
        self.data = trade_data
        self.party_view = trade_view
        self.value = None

    async def on_timeout(self):
        cmd = "btn.confirm.delete"
        try:
            await self.interact.edit_original_response(
                content=ts.get(f"cmd.err-timeout"), view=None
            )
            await save_log(
                pool=self.interact.client.db,
                type=LOG_TYPE.event,
                cmd=cmd,
                interact=self.interact,
                msg=f"TradeView.ConfirmDeleteView -> timeout",
            )
        except discord.NotFound:
            await save_log(
                pool=self.interact.client.db,
                type=LOG_TYPE.warn,
                cmd=cmd,
                interact=self.interact,
                msg=f"TradeView.ConfirmDeleteView -> timeout, but Not Found",
            )
        except Exception:
            await save_log(
                pool=self.interact.client.db,
                type=LOG_TYPE.err,
                cmd=cmd,
                interact=self.interact,
                msg=f"TradeView.ConfirmDeleteView -> timeout, but ERR",
                obj=return_traceback(),
            )

    @ui.button(label=ts.get(f"{pf}del-btny"), style=discord.ButtonStyle.danger)
    async def yes_button(self, interact: discord.Interaction, button: ui.Button):
        await interact.response.defer(ephemeral=True)
        await interact.delete_original_response()
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd="btn.confirm.delete",
            interact=interact,
            msg=f"ConfirmDeleteView -> clicked yes",
        )
        try:
            await add_job(
                JobType.TRADE_DELETE,
                {"interact": interact, "origin_msg": self.origin_message},
            )
            await interact.client.trigger_queue_processing()
        except Exception:
            await interact.followup.send(
                ts.get(f"{pf}err-general"), view=SupportView(), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd="btn.confirm.delete",
                interact=interact,
                msg=f"ConfirmDeleteView -> clicked yes, but ERR",
                obj=return_traceback(),
            )
        self.value = True
        self.stop()

    @ui.button(label=ts.get(f"{pf}del-btnn"), style=discord.ButtonStyle.secondary)
    async def no_button(self, interact: discord.Interaction, button: ui.Button):
        await interact.response.edit_message(content=ts.get(f"{pf}canceled"), view=None)
        self.value = False
        self.stop()
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd="btn.confirm.delete.cancel",
            interact=interact,
            msg=f"ConfirmDeleteView -> clicked no",
        )


class ConfirmTradeView(ui.View):
    def __init__(self, db_pool, trade_id, original_message):
        super().__init__(timeout=30)
        self.db_pool = db_pool
        self.trade_id = trade_id
        self.original_message = original_message
        self.value = None

    @ui.button(label=ts.get(f"{pf}btn-confirm"), style=discord.ButtonStyle.success)
    async def yes_button(self, interact: discord.Interaction, button: ui.Button):
        await interact.response.defer(ephemeral=True)
        await interact.delete_original_response()
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd="btn.confirm.trade",
            interact=interact,
            msg=f"ConfirmTradeView -> YES",
        )
        try:
            trade_info = await TradeService.get_trade_by_id(self.db_pool, self.trade_id)

            req_text: str = ""
            # req_text += await WarnService.generateWarnMsg(interact.client.db, interact.user.id)
            req_text += ts.get(f"{pf}trade-request").format(
                host_mention=f"<@{trade_info['host_id']}>",
                user_mention=interact.user.mention,
                user=parseNickname(interact.user.display_name),
                price=trade_info["price"],
                type=revTradeType(trade_info["trade_type"]),
            )
            await self.original_message.channel.send(req_text)
            self.value = True
            self.stop()
        except Exception:
            await interact.followup.send(
                ts.get(f"{pf}err-general"), view=SupportView(), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd="btn.confirm.trade",
                interact=interact,
                msg=f"ConfirmTradeView -> ERR",
                obj=return_traceback(),
            )

    @ui.button(label=ts.get(f"{pf}btn-cancel"), style=discord.ButtonStyle.secondary)
    async def no_button(self, interact: discord.Interaction, button: ui.Button):
        await interact.response.edit_message(content=ts.get(f"{pf}canceled"), view=None)
        self.value = False
        self.stop()
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd="btn.confirm.trade.cancel",
            interact=interact,
            msg=f"ConfirmTradeView -> clicked no",
        )


class TradeView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldown_manage = commands.CooldownMapping.from_cooldown(
            1, COOLDOWN_SHORT, commands.BucketType.user
        )
        self.cooldown_call = commands.CooldownMapping.from_cooldown(
            1, COOLDOWN_BTN_CALL, commands.BucketType.user
        )

    @staticmethod
    async def check_permissions(interact, trade_data, cmd: str = ""):
        is_host = interact.user.id == trade_data["host_id"]
        is_admin = await is_admin_user(interact, notify=False, cmd=cmd)
        if not is_host:
            if not is_admin:
                await interact.response.send_message(
                    ts.get(f"{pf}err-only-host"), ephemeral=True
                )
                return False
        return True

    @staticmethod
    async def basic_trade_logic(interact, cd, cmd: str) -> bool | dict:
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd="TradeView btn",
            interact=interact,
            msg=cmd,
        )
        if await is_cooldown(interact, cd):
            return False
        if await is_banned_user(interact):
            return False
        if not await check_consent(interact):
            return False

        trade_data = await TradeService.get_trade_by_message_id(
            interact.client.db, interact.message.id
        )
        if not await isTradeExists(interact, trade_data):
            return False

        return trade_data

    # btn trade request
    @ui.button(
        label=ts.get(f"{pf}btn-trade"),
        style=discord.ButtonStyle.primary,
        custom_id="trade_btn_trade",
    )
    async def trade_action(self, interact: discord.Interaction, button: ui.Button):
        cmd: str = "TradeView -> trade_action"
        trade_data = await self.basic_trade_logic(interact, self.cooldown_call, cmd)
        if not trade_data:
            return

        if interact.user.id == trade_data["host_id"]:
            await interact.response.send_message(
                ts.get(f"{pf}err-self-trade"), ephemeral=True
            )
            return

        view = ConfirmTradeView(interact.client.db, trade_data["id"], interact.message)
        await interact.response.send_message(
            ts.get(f"{pf}confirm-trade"), view=view, ephemeral=True
        )
        timed_out = await view.wait()
        if timed_out:
            try:
                await interact.edit_original_response(
                    content=ts.get(f"{pf}pv-del-cancel"), view=None
                )
            except discord.errors.NotFound:
                pass

    # btn edit trade info
    @ui.button(
        label=ts.get(f"{pf}btn-edit-info"),
        style=discord.ButtonStyle.secondary,
        custom_id="trade_btn_edit_info",
    )
    async def edit_trade_info(self, interact: discord.Interaction, button: ui.Button):
        cmd = "TradeView -> edit_trade_info"
        trade_data = await self.basic_trade_logic(interact, self.cooldown_manage, cmd)
        if not trade_data:
            return

        if not await self.check_permissions(interact, trade_data, cmd):
            return

        await interact.response.send_modal(
            EditTradeModal(trade_data, interact, interact.client.db)
        )

    # edit nickname
    @ui.button(
        label=ts.get(f"{pf}btn-edit-nickname"),
        style=discord.ButtonStyle.secondary,
        custom_id="trade_btn_edit_nick",
    )
    async def edit_nickname(self, interact: discord.Interaction, button: ui.Button):
        cmd = "TradeView -> edit_nickname"
        trade_data = await self.basic_trade_logic(interact, self.cooldown_manage, cmd)
        if not trade_data:
            return

        if not await is_admin_user(interact, notify=False, cmd=cmd):
            await interact.response.send_message(
                ts.get(f"general.unable"), ephemeral=True
            )
            return

        await interact.response.send_modal(
            EditNicknameModal(trade_data["game_nickname"], interact, interact.client.db)
        )

    # btn close trade
    @ui.button(
        label=ts.get(f"{pf}btn-close"),
        style=discord.ButtonStyle.danger,
        custom_id="trade_btn_edit_close",
    )
    async def close_trade(self, interact: discord.Interaction, button: ui.Button):
        cmd = "TradeView -> close_trade"
        trade_data = await self.basic_trade_logic(interact, self.cooldown_manage, cmd)
        if not trade_data:
            return

        if not await self.check_permissions(interact, trade_data, cmd):
            return

        trade_data["host_mention"] = f"<@{trade_data['host_id']}>"
        view = ConfirmDeleteView(interact, interact.message, trade_data, self)
        await interact.response.send_message(
            ts.get(f"{pf}confirm-delete"), view=view, ephemeral=True
        )
