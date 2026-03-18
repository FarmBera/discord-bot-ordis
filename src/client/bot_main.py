import datetime as dt
import json
import os
from collections import defaultdict

import aiohttp
import discord
from discord.ext import commands, tasks

from config.TOKEN import base_url_profile
from config.config import LOG_TYPE
from src.bot_translator import BotTranslator
from src.commands.noti_channel import DB_COLUMN_MAP, PROFILE_CONFIG
from src.constants.color import C
from src.constants.keys import MSG_BOT
from src.services.party_service import PartyService
from src.services.queue_manager import GLOBAL_QUEUE, JobType
from src.services.trade_service import TradeService
from src.translator import ts
from src.utils.data_manager import SETTINGS
from src.utils.db_helper import query_reader
from src.utils.delay import delay
from src.utils.discord_file import img_file
from src.utils.logging_utils import save_log
from src.utils.return_err import return_traceback
from src.utils.times import timeNowDT
from src.views.party_view import PartyView
from src.views.trade_view import TradeView


class DiscordBot(commands.Bot):
    def __init__(self, *, intents: discord.Intents, db, **options):
        super().__init__(command_prefix="!", intents=intents, **options)
        self.db = db
        self.webhook_cache = {}
        self.processing: bool = False

    async def setup_hook(self) -> None:
        self.add_view(PartyView())
        self.add_view(TradeView())
        print(
            f"{C.blue}[{LOG_TYPE.info}] {C.green}Persistent Views successfully registered.{C.default}"
        )
        # load translator
        await self.tree.set_translator(BotTranslator())
        # load cogs
        cog_ext = [
            # commands
            "register",
            "party",
            "trade",
            "complain",
            "user_warn",
            "voice_log",
            # tasks
            "tasks.week_start_noti",
            "tasks.check_new_content",
            "tasks.auto_party_expire",
            "tasks.auto_trade_expire",
        ]
        for ext in cog_ext:
            try:
                await self.load_extension(f"src.cogs.{ext}")
                print(ext)
            except Exception as e:
                print(f"{C.red}Failed to load extension {ext}: {e}{C.default}")

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
            print(f"{C.blue}[{LOG_TYPE.err}] {C.red}Commands Not Synced!")

        # noinspection PyTypeChecker
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(ts.get("start.bot-status-msg")),
        )
        print(
            f"{C.blue}[{LOG_TYPE.info}] {C.cyan}{ts.get('start.final')} <<{C.white}{self.user}{C.cyan}>>"
        )
        print(f"{C.green}{ts.get(f'start.final2')}{C.default}")
        await save_log(
            pool=self.db,
            cmd="bot.BOOTED",
            user=MSG_BOT,
            msg=f"[{LOG_TYPE.info}] Bot booted up.",
        )
        # start coroutine
        if not SETTINGS["noti"]["isEnabled"]:
            return

        print(
            f"{C.blue}[{LOG_TYPE.info}] {C.green}{ts.get('start.coroutine')}{C.default}"
        )
        print(C.white, timeNowDT(), C.default, sep="")

    async def send_alert(
        self, value: discord.Embed | tuple[discord.Embed, str] | str, channel_list: list
    ) -> None:
        # send message
        for ch in channel_list:
            try:
                channel = self.get_channel(ch)
                msg: str = f"msg sent"
                if isinstance(value, discord.Embed):
                    await save_log(
                        pool=self.db,
                        type=LOG_TYPE.msg,
                        cmd="auto_sent_message",
                        user=MSG_BOT,
                        guild=channel.guild.name,
                        channel=channel.name,
                        msg=msg,
                        obj=value.description,
                    )
                    await channel.send(embed=value)
                elif isinstance(value, tuple):  # embed with file
                    eb, f = value
                    await save_log(
                        pool=self.db,
                        type=LOG_TYPE.msg,
                        cmd="auto_sent_message",
                        user=MSG_BOT,
                        guild=channel.guild.name,
                        channel=channel.name,
                        msg=msg,
                        obj=eb.description,
                    )
                    f = img_file(f)
                    await channel.send(embed=eb, file=f)
                else:  # string type
                    await save_log(
                        pool=self.db,
                        type=LOG_TYPE.msg,
                        cmd="auto_sent_message",
                        user=MSG_BOT,
                        guild=channel.guild.name,
                        channel=channel.name,
                        msg=msg,
                        obj=value,
                    )
                    await channel.send(value)
            except Exception as e:
                error_msg = f"[Error] error on sending in {ch}: {e}"
                print(f"{C.red}{error_msg}{C.default}")
                await save_log(
                    pool=self.db,
                    type=LOG_TYPE.err,
                    cmd="send_alert",
                    user=MSG_BOT,
                    msg=error_msg,
                    obj=return_traceback(),
                )

    async def get_profile_img(self, noti_key):
        out_name = self.user.name
        out_avatar = self.user.display_avatar.url if self.user else None

        # get profile config
        profile_conf = PROFILE_CONFIG.get(noti_key)
        if not profile_conf:
            return out_name, out_avatar

        # get profile name
        fetched_name = profile_conf.get("name")
        fetched_avatar = profile_conf.get("avatar")
        if (not fetched_name) or (not fetched_avatar):
            return out_name, out_avatar

        out_name = fetched_name
        out_avatar = base_url_profile + fetched_avatar
        # fetch url & combine
        # async with transaction(self.db) as cursor:
        #     await cursor.execute("SELECT value FROM vari WHERE name='img_server'")
        #     base_url = await cursor.fetchone()
        # if base_url:
        #     out_avatar = f"{base_url["value"]}/?name={fetched_avatar}"

        return out_name, out_avatar

    async def broadcast_webhook(
        self, noti_key: str, content=None, arg_func=None, content_factory=None
    ) -> None:
        """
        search the webhook subscribed to that notification (noti_key) in the database and sends it.

        content_factory: optional callable(lang: str) -> content
            When provided, content is generated per-language group.
            When omitted, the pre-built `content` is sent to all subscribers (legacy behavior).
        """
        # check db column mapping
        db_column = DB_COLUMN_MAP.get(noti_key)
        if not db_column:
            msg = f"[{LOG_TYPE.err}] Unmapped notification key: `{noti_key}` -> {db_column}"
            await save_log(
                pool=self.db,
                type=LOG_TYPE.err,
                cmd="broadcast_webhook",
                user=MSG_BOT,
                msg=msg,
            )
            print(C.yellow, msg, C.default, sep="")
            return

        # search subscribers in db
        async with query_reader(self.db) as cursor:
            await cursor.execute(
                f"SELECT webhook_url, lang FROM webhooks WHERE {db_column} = 1"
            )
            subscribers = await cursor.fetchall()

        if not subscribers:
            return

        # group subscribers by language
        lang_groups = defaultdict(list)
        for row in subscribers:
            subscriber_lang = row.get("lang", "ko")
            lang_groups[subscriber_lang].append(row)

        # initialize counters
        total_subscribers = len(subscribers)
        success_count = 0
        log_content = ""

        # setup profile
        final_username, final_avatar_url = await self.get_profile_img(noti_key)

        # send alert & check result
        async with aiohttp.ClientSession() as session:
            eta_start: dt.datetime = timeNowDT()

            for subscriber_lang, rows in lang_groups.items():
                # generate content for this language
                lang_content = (
                    content_factory(subscriber_lang) if content_factory else content
                )
                if lang_content is None:
                    continue

                # prepare payload data for this language group
                embed_data = None
                text_content = ""
                files_to_upload = []
                content_file_name = "i.webp"

                # process embed
                if isinstance(lang_content, discord.Embed):
                    embed_data = lang_content.to_dict()
                    log_content = lang_content.description

                # process tuple (embed, file)
                elif isinstance(lang_content, tuple):
                    eb, file_info = lang_content
                    embed_data = eb.to_dict()
                    real_file_path = None

                    log_content = f"IMG: {file_info}\n{eb.description}"
                    # img path is string
                    if isinstance(file_info, str):
                        path = f"img/{file_info}.webp"
                        if os.path.exists(path):
                            real_file_path = path

                    # read file
                    if real_file_path:
                        try:
                            with open(real_file_path, "rb") as f:
                                files_to_upload.append(
                                    {
                                        "name": "file",
                                        "filename": content_file_name,
                                        "data": f.read(),
                                    }
                                )
                        except Exception as e:
                            msg = f"Failed to read image file: {e}"
                            await save_log(
                                pool=self.db,
                                type=LOG_TYPE.err,
                                cmd="broadcast_webhook",
                                user=MSG_BOT,
                                msg=msg,
                                obj=return_traceback(),
                            )
                            print(C.red, msg, C.default)

                # string only
                else:
                    text_content = str(lang_content)
                    log_content = text_content

                if arg_func:
                    args = arg_func(subscriber_lang)

                # send to each subscriber in this language group
                for row in rows:
                    url = row["webhook_url"]

                    # verify URL
                    if not url or not str(url).startswith("http"):
                        continue

                    payload = {
                        "username": final_username,
                        "avatar_url": final_avatar_url,
                        "content": text_content.strip(),
                    }
                    if embed_data:
                        payload["embeds"] = [embed_data]
                    if arg_func:
                        payload["content"] = args

                    try:
                        if files_to_upload:
                            # [send file] multipart/form-data
                            form = aiohttp.FormData()
                            form.add_field("payload_json", json.dumps(payload))

                            # upload all file
                            for file_obj in files_to_upload:
                                form.add_field(
                                    file_obj["name"],
                                    file_obj["data"],
                                    filename=file_obj["filename"],
                                    content_type="application/octet-stream",
                                )

                            async with session.post(url, data=form) as response:
                                if 200 <= response.status < 300:
                                    success_count += 1
                                else:
                                    err_text = await response.text()
                                    eta_end: dt.timedelta = timeNowDT() - eta_start
                                    await save_log(
                                        pool=self.db,
                                        type=LOG_TYPE.err,
                                        cmd="broadcast_webhook",
                                        user=MSG_BOT,
                                        msg=f"Failed to send {noti_key} Multipart (code: {response.status}, eta: {eta_end})",
                                        obj=err_text,
                                    )
                        else:  # general send (json)
                            async with session.post(url, json=payload) as response:
                                if 200 <= response.status < 300:
                                    success_count += 1
                                else:
                                    err_text = await response.text()
                                    eta_end: dt.timedelta = timeNowDT() - eta_start
                                    await save_log(
                                        pool=self.db,
                                        type=LOG_TYPE.err,
                                        cmd="broadcast_webhook",
                                        user=MSG_BOT,
                                        msg=f"Failed to send {noti_key} general (code: {response.status}, eta: {eta_end})",
                                        obj=err_text,
                                    )

                    except Exception as e:
                        eta_sending: dt.timedelta = timeNowDT() - eta_start
                        await save_log(
                            pool=self.db,
                            type=LOG_TYPE.err,
                            cmd="broadcast_webhook",
                            user=MSG_BOT,
                            msg=f"ERROR on sending msg: {noti_key} (eta: {eta_sending})\n{e}",
                            obj=return_traceback(),
                        )

        # logging
        eta_sending: dt.timedelta = timeNowDT() - eta_start
        log_msg = (
            f"{noti_key} sent. {success_count}/{total_subscribers} (eta: {eta_sending})"
        )
        await save_log(
            pool=self.db,
            type=LOG_TYPE.msg,
            cmd="broadcast_webhook",
            user=MSG_BOT,
            msg=log_msg,
            obj=f"{log_content}",
        )

    @tasks.loop(count=1)
    async def process_queue(self):
        try:
            while GLOBAL_QUEUE:
                job = GLOBAL_QUEUE.pop(0)  # FIFO
                job_type = job["type"]
                data = job["data"]

                try:
                    if job_type == JobType.PARTY_CREATE:
                        await PartyService.execute_create(self.db, data)
                    elif job_type == JobType.PARTY_UPDATE:
                        await PartyService.execute_update(self.db, data)
                    elif job_type == JobType.PARTY_DELETE:
                        await PartyService.execute_delete(self.db, data)
                    elif job_type == JobType.PARTY_TOGGLE:
                        await PartyService.execute_toggle(self.db, data)
                    elif job_type == JobType.TRADE_CREATE:
                        await TradeService.execute_create(self.db, data)
                    elif job_type == JobType.TRADE_UPDATE:
                        await TradeService.execute_update(self.db, data)
                    elif job_type == JobType.TRADE_DELETE:
                        await TradeService.execute_delete(self.db, data)
                except Exception as inner_e:
                    msg = f"Error executing job {job_type}: {inner_e}"
                    print(msg)
                    await save_log(
                        pool=self.db,
                        type=LOG_TYPE.err,
                        cmd="process_queue.inner",
                        msg=msg,
                        obj=return_traceback(),
                    )
                # print(len(GLOBAL_QUEUE))  # DEBUG_CODE
                await delay()

        except Exception as e:
            msg = f"Failed to process queue: {e}"
            print(msg)
            await save_log(
                pool=self.db,
                type=LOG_TYPE.err,
                cmd="bot.process_queue",
                msg=msg,
                obj=return_traceback(),
            )

    async def trigger_queue_processing(self):
        if not self.process_queue.is_running():
            self.process_queue.start()
