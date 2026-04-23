import discord
from discord import app_commands
from discord.ext import commands

from config.config import LOG_TYPE
from src.constants.keys import COOLDOWN_CREATE
from src.parser.marketsearch import get_slug_data, get_market_item_names
from src.services.channel_service import ChannelService
from src.services.queue_manager import add_job, JobType
from src.services.trade_service import TradeService, MarketAPIError
from src.translator import ts
from src.utils.api_request import API_MarketSearch
from src.utils.logging_utils import save_log
from src.utils.permission import is_banned_user
from src.utils.return_err import return_traceback
from src.views.consent_view import check_consent
from src.views.help_view import SupportView
from src.views.trade_view import parseNickname

pf = "cmd.trade."


class TradeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="trade", description="cmd.trade.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_CREATE, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.choices(
        trade_type=[
            app_commands.Choice(name=ts.get("cmd.trade.type-sell"), value=1),
            app_commands.Choice(name=ts.get("cmd.trade.type-buy"), value=2),
        ]
    )
    @app_commands.describe(
        trade_type="cmd.trade.desc-trade-type",
        item_name="cmd.trade.desc-item-name",
        item_rank="cmd.trade.desc-item-rank",
        # game_nickname="cmd.trade.desc-nickname",
        price="cmd.trade.desc-price",
        quantity="cmd.trade.desc-quantity",
    )
    async def cmd_create_trade(
        self,
        interact: discord.Interaction,
        trade_type: app_commands.Choice[int],
        item_name: str,
        # game_nickname: str = "",
        item_rank: int = 0,
        price: int = 0,
        quantity: int = 1,
    ):
        await interact.response.defer(ephemeral=True)

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
                cmd=f"cmd.trade",
                interact=interact,
                msg="cmd used, but unregistered server",
            )
            return

        # fetch channel
        target_channel = self.bot.get_channel(channel_list.get("trade_ch"))
        if not target_channel:
            await interact.followup.send(ts.get("cmd.ch-not-found"), ephemeral=True)
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd=f"cmd.trade",
                interact=interact,
                msg="trade channel not found",
            )
            return

        # search item & verify
        flag, item_slug, real_item_name, _ = get_slug_data(item_name)
        if not flag:
            await interact.followup.send(
                ts.get("cmd.market-search.no-result").format(name=item_name),
                ephemeral=True,
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.warn,
                cmd=f"cmd.trade",
                interact=interact,
                msg=f"'{item_name}' not found in market",
            )
            return

        # setup price
        try:
            market_res = await API_MarketSearch(self.bot.db, item_slug)

            estimated_price, market_data, output_msg = (
                await TradeService.estimate_price(market_res, item_rank, price)
            )
        except MarketAPIError as e:
            await interact.followup.send(
                ts.get(f"{pf}err-api"), view=SupportView(), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.warn,
                cmd="cmd.trade",
                interact=interact,
                msg=f"Market API unavailable: {e} (status={e.status_code})",
            )
            return
        except Exception as e:
            await interact.followup.send(
                ts.get(f"{pf}err-api"), view=SupportView(), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd="cmd.trade",
                interact=interact,
                msg=f"Market API error: {e}",
                obj=return_traceback(),
            )
            return

        # setup automatic nickname
        final_nickname = parseNickname(interact.user.display_name)
        # game_nickname if game_nickname else parseNickname(interact.user.display_name)

        if market_data:
            is_rank_item = True if market_data[0].get("rank") is not None else False
        else:
            is_rank_item = False

        if not is_rank_item:
            item_rank = -1

        # save to db
        try:
            trade_id = await TradeService.create_trade(
                self.bot.db,
                interact.user.id,
                final_nickname,
                trade_type.name,
                real_item_name,
                item_rank,
                quantity,
                estimated_price,
            )
        except Exception as e:
            await interact.followup.send(
                ts.get("cmd.err-db"), view=SupportView(), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd=f"cmd.trade",
                interact=interact,
                msg=f"db insertion error: {e}",
                obj=return_traceback(),
            )
            return

        # add to queue for processing
        data = {
            "id": trade_id,
            "host_id": interact.user.id,
            "host_mention": interact.user.mention,
            "game_nickname": final_nickname,
            "trade_type": trade_type.name,
            "item_name": real_item_name,
            "item_rank": item_rank,
            "quantity": quantity,
            "price": estimated_price,
            "isRank": is_rank_item,
        }
        await add_job(
            JobType.TRADE_CREATE,
            {"interact": interact, "data": data, "target_channel": target_channel},
        )
        await interact.followup.send(
            f"{output_msg}✅ '{target_channel.mention}' {ts.get(f'{pf}created-trade')}",
            ephemeral=True,
        )
        await self.bot.trigger_queue_processing()

    # auto complete item
    # noinspection PyUnusedLocal
    @cmd_create_trade.autocomplete("item_name")
    async def trade_item_name_autocomplete(
        self, interact: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        choices = [
            app_commands.Choice(name=name, value=name)
            for name in get_market_item_names()
            if current.lower() in name.lower()
        ]
        return choices[:25]


async def setup(bot: commands.Bot):
    await bot.add_cog(TradeCog(bot))
