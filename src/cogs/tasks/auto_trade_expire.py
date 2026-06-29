import datetime as dt

import discord
from discord.ext import tasks, commands

from config.config import LOG_TYPE, language as lang, Lang
from src.constants.color import C
from src.constants.keys import MSG_BOT, LFG_WEBHOOK_NAME
from src.services.trade_service import TradeService
from src.translator import ts
from src.utils.db_helper import query_reader
from src.utils.delay import delay
from src.utils.logging_utils import save_log
from src.utils.return_err import return_traceback
from src.utils.times import KST, timeNowDT
from src.views.trade_view import build_trade_embed_from_db


class tasks_auto_trade_expire(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # automatic trade delete
        if lang == Lang.KO and not self.auto_trade_expire.is_running():
            self.auto_trade_expire.start()
            print(
                f"{C.blue}[{LOG_TYPE.info}] {C.green}{ts.get('start.crt-each')}",
                "auto_trade_expire",
            )

    async def cog_unload(self):
        self.auto_trade_expire.cancel()

    # trade auto expire
    @tasks.loop(time=dt.time(hour=4, minute=0, tzinfo=KST))
    async def auto_trade_expire(self) -> None:
        # await save_log(
        #     pool=self.bot.db,
        #     type=LOG_TYPE.info,
        #     cmd="auto_trade_expire()",
        #     user=MSG_BOT,
        #     msg=f"START Trade AutoDelete",
        # )
        deleted_count: int = 0
        eta: dt.datetime = timeNowDT()

        async with query_reader(self.bot.db) as cursor:
            await cursor.execute("SELECT value FROM vari WHERE name='trade_exp_time'")
            trade_exp_time = await cursor.fetchone()
            trade_exp_time = int(trade_exp_time["value"])

        # delete time
        expiration_time = timeNowDT() - dt.timedelta(days=trade_exp_time)

        # fetch all message from db
        async with query_reader(self.bot.db) as cursor:
            await cursor.execute(
                "SELECT id, thread_id, message_id FROM trade WHERE updated_at < %s",
                (expiration_time,),
            )
            expired_trades = await cursor.fetchall()

        for trade in expired_trades:
            try:
                thread = await self.bot.fetch_channel(trade["thread_id"])
                await thread.edit(locked=True)  # lock thread
                await delay()

                msg = await thread.fetch_message(trade["message_id"])
                await delay()

                new_embed = await build_trade_embed_from_db(
                    msg.id, self.bot.db, isDelete=True
                )
                await msg.edit(embed=new_embed, view=None)
                await delay()

                # edit web hook msg
                webhooks = await thread.parent.webhooks()
                webhook = discord.utils.get(webhooks, name=LFG_WEBHOOK_NAME)
                await delay()

                if webhook:
                    starter_message = await thread.parent.fetch_message(thread.id)
                    if starter_message:
                        await webhook.edit_message(
                            message_id=thread.id,
                            content=ts.get("cmd.trade.expired"),
                        )
                await delay()

                await TradeService.delete_trade(self.bot.db, trade["thread_id"])
                deleted_count += 1
                # omsg = f"Expired trade {trade['id']} deleted."
                # await save_log(
                #     pool=self.bot.db,
                #     type=LOG_TYPE.info,
                #     cmd="auto_trade_expire()",
                #     user=MSG_BOT,
                #     msg=omsg,
                # )
            except discord.NotFound:  # msg deleted manually
                await save_log(
                    pool=self.bot.db,
                    type=LOG_TYPE.warn,
                    cmd="auto_trade_expire()",
                    user=MSG_BOT,
                    msg=f"Trade AutoDelete, but msg not found: {trade['id']}",
                    obj=return_traceback(),
                )
                await TradeService.delete_trade(self.bot.db, trade["thread_id"])
            except Exception as e:
                await save_log(
                    pool=self.bot.db,
                    type=LOG_TYPE.err,
                    cmd="auto_trade_expire()",
                    user=MSG_BOT,
                    msg=f"Trade AutoDelete, but error occurred! {e}",
                    obj=return_traceback(),
                )
            await delay()

        if deleted_count >= 1:
            await save_log(
                pool=self.bot.db,
                type=LOG_TYPE.info,
                cmd="auto_trade_expire()",
                user=MSG_BOT,
                msg=f"END Trade AutoDelete (deleted: {deleted_count}, eta: {timeNowDT()-eta})",
            )


async def setup(bot):
    await bot.add_cog(tasks_auto_trade_expire(bot))
