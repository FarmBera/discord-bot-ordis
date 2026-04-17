import discord

from config.config import LOG_TYPE
from src.parser.marketsearch import categorize
from src.translator import ts
from src.utils.api_request import API_MarketSearch
from src.utils.db_helper import transaction, query_reader
from src.utils.delay import delay
from src.utils.logging_utils import save_log
from src.utils.webhook import webhook_send, webhook_edit

pf = "cmd.trade."


class TradeService:
    @staticmethod
    async def get_trade_by_message_id(pool, message_id: int):
        async with query_reader(pool) as cursor:
            await cursor.execute(
                "SELECT * FROM trade WHERE message_id = %s", (message_id,)
            )
            return await cursor.fetchone()

    @staticmethod
    async def get_trade_by_id(pool, trade_id: int):
        async with query_reader(pool) as cursor:
            await cursor.execute("SELECT * FROM trade WHERE id = %s", (trade_id,))
            return await cursor.fetchone()

    @staticmethod
    async def create_trade(
        pool, host_id, game_nickname, trade_type, item_name, item_rank, quantity, price
    ):
        async with transaction(pool) as cursor:
            await cursor.execute(
                "INSERT INTO trade (host_id, game_nickname, trade_type, item_name, item_rank, quantity, price) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (
                    host_id,
                    game_nickname,
                    trade_type,
                    item_name,
                    item_rank,
                    quantity,
                    price,
                ),
            )
            return cursor.lastrowid

    @staticmethod
    async def update_thread_info(pool, trade_id, thread_id, message_id):
        async with transaction(pool) as cursor:
            await cursor.execute(
                "UPDATE trade SET thread_id = %s, message_id = %s WHERE id = %s",
                (thread_id, message_id, trade_id),
            )

    @staticmethod
    async def update_nickname(pool, message_id, new_nickname):
        async with transaction(pool) as cursor:
            await cursor.execute(
                "UPDATE trade SET game_nickname = %s WHERE message_id = %s",
                (new_nickname, message_id),
            )

    @staticmethod
    async def update_quantity(pool, message_id, new_quantity):
        async with transaction(pool) as cursor:
            await cursor.execute(
                "UPDATE trade SET quantity = %s WHERE message_id = %s",
                (new_quantity, message_id),
            )

    @staticmethod
    async def update_price(pool, message_id, new_price):
        async with transaction(pool) as cursor:
            await cursor.execute(
                "UPDATE trade SET price = %s WHERE message_id = %s",
                (new_price, message_id),
            )

    @staticmethod
    async def update_item_rank(pool, message_id, new_rank):
        async with transaction(pool) as cursor:
            await cursor.execute(
                "UPDATE trade SET item_rank = %s WHERE message_id = %s",
                (new_rank, message_id),
            )

    @staticmethod
    async def delete_trade(pool, thread_id):
        async with transaction(pool) as cursor:
            await cursor.execute("DELETE FROM trade WHERE thread_id = %s", (thread_id,))

    @staticmethod
    async def estimate_price(
        pool, trade_type, item_slug, item_rank, input_price
    ) -> tuple[int, list, str]:
        output_msg: str = ""
        # get market price
        market_api_result = await API_MarketSearch(pool, item_slug)
        market = categorize(market_api_result.json(), rank=item_rank)

        if market_api_result.status_code == 404:
            output_msg += f"{ts.get(f'{pf}err-no-market')}\n\n"
            return (input_price if input_price else 0), market, output_msg
        elif market_api_result.status_code != 200:
            raise ValueError("Market API resp-code is not 200")

        if input_price:
            return input_price, market, output_msg

        # automatic price decision
        price_list = []
        length = len(market)
        for i in range(min(length, 6)):
            price_list.append(market[i]["platinum"])

        estimated_price = sum(price_list) // len(price_list) if price_list else 0
        output_msg += f"{ts.get(f'{pf}auto-price').format(price=estimated_price)}\n\n"

        return estimated_price, market, output_msg

    ############################
    ############################
    @staticmethod
    async def execute_create(db, job_data):
        from src.views.trade_view import TradeView, build_trade_embed

        interact = job_data["interact"]
        data = job_data["data"]
        target_channel = job_data["target_channel"]
        avatar = interact.client.user.avatar

        thread_name = f"[{data['trade_type']}] {data['item_name']}"
        if data.get("isRank") and data["item_rank"] != -1:
            thread_name += (
                f" ({ts.get(f'{pf}rank-simple').format(rank=data['item_rank'])})"
            )

        thread_starter_msg = await webhook_send(
            target_channel,
            avatar,
            content=f"**{data['trade_type']}** 합니다.",
            username=interact.user.display_name,
            avatar_url=interact.user.display_avatar.url,
            wait=True,
        )
        thread = await thread_starter_msg.create_thread(
            name=thread_name,
            reason=f"{interact.user.display_name} user created trade",
        )
        embed = await build_trade_embed(data, db, isRank=data.get("isRank", False))
        msg = await thread.send(embed=embed, view=TradeView())

        await TradeService.update_thread_info(db, data["id"], thread.id, msg.id)
        await save_log(
            pool=db,
            type=LOG_TYPE.cmd,
            cmd="trade",
            interact=interact,
            msg="Trade Created",
            obj=embed.description,
        )

    @staticmethod
    async def execute_update(db, job_data):
        from src.views.trade_view import build_trade_embed_from_db

        interact = job_data.get("interact")
        if interact:
            new_embed = await build_trade_embed_from_db(interact.message.id, db)
            await interact.message.edit(embed=new_embed)
        else:
            msg = job_data["origin_msg"]
            new_embed = await build_trade_embed_from_db(msg.id, db)
            await msg.edit(embed=new_embed)

    @staticmethod
    async def execute_delete(db, job_data):
        from src.views.trade_view import build_trade_embed_from_db

        msg = job_data["origin_msg"]
        interact = job_data["interact"]
        new_embed = await build_trade_embed_from_db(msg.id, db, isDelete=True)
        await msg.edit(embed=new_embed, view=None)
        await delay()

        parent_channel = interact.channel.parent
        avatar = interact.client.user.avatar

        await webhook_edit(
            parent_channel,
            avatar,
            message_id=interact.channel.id,
            content=ts.get(f"{pf}deleted"),
        )
        await delay()

        # lock thread
        if isinstance(interact.channel, discord.Thread):
            await interact.channel.edit(locked=True)

        await TradeService.delete_trade(db, interact.channel.id)
        await save_log(
            pool=db,
            type=LOG_TYPE.info,
            cmd="btn.confirm.delete",
            interact=interact,
            msg=f"Trade Deleted",
            obj=new_embed.description,
        )
