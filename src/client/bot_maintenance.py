import discord
from discord.ext import commands

# from src.main import tree
from config.config import LOG_TYPE
from src.bot_translator import BotTranslator
from src.constants.color import C
from src.constants.keys import MSG_BOT
from src.translator import ts
from src.utils.db_helper import transaction
from src.utils.logging_utils import save_log
from src.utils.times import timeNowDT
from src.views.maintenance_view import PartyView, TradeView


class MaintanceBot(commands.Bot):
    def __init__(self, *, intents: discord.Intents, db, **options):
        super().__init__(command_prefix="!", intents=intents, **options)
        self.db = db

    async def setup_hook(self) -> None:
        self.add_view(PartyView())
        self.add_view(TradeView())
        print(
            f"{C.magenta}Persistent Views successfully registered for maintenance mode.{C.default}"
        )
        # load translator
        await self.tree.set_translator(BotTranslator())
        await self.load_extension(f"src.cogs.maintenance")

    async def on_ready(self) -> None:
        print(
            f"{C.blue}[{LOG_TYPE.info}] {C.yellow}{ts.get('start.sync')}...{C.default}",
            end="",
        )
        await self.wait_until_ready()

        if self.tree:
            await self.tree.sync()
            print(f"{C.green}Synced Tree Commands")
        else:
            print(f"{C.blue}[{LOG_TYPE.info}] {C.red}Commands Not Synced!")

        await self.change_presence(
            status=discord.Status.do_not_disturb,
            activity=discord.Game(ts.get("maintenance.bot-status-msg")),
        )
        print(
            f"{C.blue}[{LOG_TYPE.info}] {C.cyan}{ts.get('start.final')} <<{C.white}{self.user}{C.cyan}>>"
        )
        print(f"{C.green}{ts.get(f'start.final2')}{C.default}")

        async with transaction(self.db) as cursor:
            await cursor.execute(
                "UPDATE vari SET value = CURRENT_TIMESTAMP() WHERE name = 'start_time'"
            )

        print(f"{C.blue}[info] {C.magenta}Bot is on Maintance Mode!{C.default}")
        await save_log(
            pool=self.db,
            cmd="bot.BOOTED",
            user=MSG_BOT,
            msg="[info] Bot booted up with maintance mode",
            time=timeNowDT(),
        )  # VAR
