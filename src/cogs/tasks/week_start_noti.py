import datetime as dt

from discord.ext import tasks, commands

from config.config import LOG_TYPE, language as lang, Lang
from config.roles import ROLES, CHANNELS
from src.constants.color import C
from src.constants.keys import MSG_BOT, DUVIRI_ROTATION, STEELPATH
from src.parser.duviriRotation import (
    w_duviri_warframe,
    w_duviri_incarnon,
)
from src.parser.steelPath import w_steelPath
from src.translator import ts
from src.utils.data_manager import get_obj_async
from src.utils.logging_utils import save_log
from src.utils.return_err import return_traceback
from src.utils.times import KST


class TASKSweek_start_noti(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        # week start noti (for KO only)
        if not self.week_start_noti.is_running():
            self.week_start_noti.start()
            print(
                f"{C.blue}[{LOG_TYPE.info}] {C.green}{ts.get('start.crt-each')}",
                "week_start_noti (teshin & custom circuit)",
            )

    async def cog_unload(self):
        self.week_start_noti.cancel()

    # weekly alert
    @tasks.loop(time=dt.time(hour=9, minute=5, tzinfo=KST))
    async def week_start_noti(self) -> None:
        # only week start (monday)
        if dt.datetime.now(dt.timezone.utc).weekday() != 0:
            return

        # log when execution
        await save_log(
            pool=self.bot.db,
            type=LOG_TYPE.info,
            cmd="week_start_noti()",
            user=MSG_BOT,
            msg="Execute week_start_noti()",
        )

        # steel essence
        steel_data = await get_obj_async(STEELPATH)
        await self.bot.broadcast_webhook(STEELPATH, w_steelPath(steel_data))

        if lang == Lang.KO:
            data_list: list = [
                w_duviri_warframe(await get_obj_async(DUVIRI_ROTATION)),
                w_duviri_incarnon(await get_obj_async(DUVIRI_ROTATION)),
            ]
            for i in range(0, len(data_list)):
                data_list[i].description = (
                    f"<@&{ROLES[i]}>\n" + data_list[i].description
                )
                try:
                    await self.bot.send_alert(data_list[i], CHANNELS)
                except Exception as e:
                    error_msg = f"[week_start_noti Error] {e}"
                    print(f"{C.red}{error_msg}{C.default}")
                    await save_log(
                        pool=self.bot.db,
                        type=LOG_TYPE.err,
                        cmd="week_start_noti()",
                        user=MSG_BOT,
                        msg=error_msg,
                        obj=return_traceback(),
                    )


async def setup(bot):
    await bot.add_cog(TASKSweek_start_noti(bot))
