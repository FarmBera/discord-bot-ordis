import asyncio

import requests
from discord.ext import tasks, commands

from config.config import LOG_TYPE, language as lang
from src.constants.color import C
from src.handler.handle_archimedea import handleDeepArchimedea, handleTemporalArchimedea
from src.handler.handle_duviri import checkCircuitWarframe, checkCircuitIncarnon
from src.handler.handle_error import handleParseError
from src.handler.handle_invasions import checkInvasions
from src.handler.handle_missing import checkExpiredItem
from src.handler.handle_missing import checkMissingIds, checkMissingItem
from src.handler.handle_news import processNews
from src.handler.handle_voidtrader import handleVoidTrader
from src.handler.handler_config import DATA_HANDLERS, LOGIC
from src.parser.archimedea import setDeepArchimedea, setTemporalArchimedea
from src.parser.bounty import handleNewBounty
from src.parser.duviriRotation import setDuvWarframe, setDuvIncarnon
from src.translator import ts, get_ts_by_lang
from src.utils.api_request import API_Request
from src.utils.data_manager import get_obj_async, set_obj_async, SETTINGS


def _make_factory(parser, *args):
    """Create a content_factory that calls parser(*args, ts=..., lang=...) for each language."""

    def factory(subscriber_lang: str):
        _ts = get_ts_by_lang(subscriber_lang)
        return parser(*args, ts=_ts, lang=subscriber_lang)

    return factory


# noinspection PyUnusedLocal,PyMethodMayBeStatic
class TASKcheck_new_content(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._dispatch = {
            LOGIC.missing: self._handle_missing,
            LOGIC.news: self._handle_news,
            LOGIC.invasions: self._handle_invasions,
            LOGIC.fissures: self._handle_fissures,
            LOGIC.duviri_wf: self._handle_duviri_wf,
            LOGIC.duviri_inc: self._handle_duviri_inc,
            LOGIC.voidtraders: self._handle_voidtraders,
            LOGIC.deep_archimedea: self._handle_deep_archimedea,
            LOGIC.temporal_archimedea: self._handle_temporal_archimedea,
            LOGIC.no_args: self._handle_no_args,
            LOGIC.bounty: self._handle_bounty,
        }

    # --- handler helpers ---

    async def _safe_parse(self, handler, log_key, *args):
        """Create a content_factory that safely calls parser with ts and lang.
        Returns factory or None on initial validation error."""
        parser = handler["parser"]

        # validate the parser works at all (with default lang)
        try:
            test_result = parser(*args, ts=ts, lang=lang)
            if test_result is None:
                return None
        except Exception as e:
            msg = f"Data parsing error in {parser}/{e}"
            await handleParseError(self.bot.db, msg, log_key)
            return None

        def factory(subscriber_lang: str):
            try:
                _ts = get_ts_by_lang(subscriber_lang)
                return parser(*args, ts=_ts, lang=subscriber_lang)
            except Exception:
                return None

        return factory

    async def _handle_missing(self, handler, origin_key, key, obj_prev, obj_new):
        should_save, newly_added_ids = checkMissingIds(obj_prev, obj_new)
        should_save = should_save or checkExpiredItem(obj_prev, obj_new)
        if not newly_added_ids:
            return None, should_save
        missing_items = checkMissingItem(obj_new, newly_added_ids)
        if not missing_items:
            return None, should_save
        factory = await self._safe_parse(handler, origin_key, missing_items)
        return factory, should_save

    async def _handle_news(self, handler, origin_key, key, obj_prev, obj_new):
        obj_prev, obj_new = processNews(obj_prev, obj_new)
        return await self._handle_missing(handler, origin_key, key, obj_prev, obj_new)

    async def _handle_invasions(self, handler, origin_key, key, obj_prev, obj_new):
        should_save, special_invasions, missing_invasions = checkInvasions(
            obj_prev, obj_new
        )
        if not special_invasions:
            return None
        factory = await self._safe_parse(handler, key, missing_invasions)
        return factory, should_save

    async def _handle_fissures(self, handler, origin_key, key, obj_prev, obj_new):
        should_save, _ = checkMissingIds(obj_prev, obj_new)
        return None, should_save

    async def _handle_duviri_wf(self, handler, origin_key, key, obj_prev, obj_new):
        if not checkCircuitWarframe(obj_new):
            return None
        try:
            await setDuvWarframe(obj_new[0])
        except Exception as e:
            msg = f"parse error in handle_duviri_rotation-1 {handler['parser']}/{e}"
            await handleParseError(self.bot.db, msg, key)
            return None
        factory = _make_factory(handler["parser"], obj_new)
        return factory, True

    async def _handle_duviri_inc(self, handler, origin_key, key, obj_prev, obj_new):
        if not checkCircuitIncarnon(obj_new):
            return None
        try:
            await setDuvIncarnon(obj_new[1])
        except Exception as e:
            msg = f"parse error in handle_duviri_rotation-2 {handler['parser']}/{e}"
            await handleParseError(self.bot.db, msg, key)
            return None
        factory = _make_factory(handler["parser"], obj_new)
        return factory, True

    async def _handle_voidtraders(self, handler, origin_key, key, obj_prev, obj_new):
        events = handleVoidTrader(obj_prev, obj_new)
        if not events:
            return None
        for event in events:
            if not SETTINGS["noti"]["list"][key]:
                continue
            embed_color = event["embed_color"]

            # build content_factory for per-language rendering
            text_key = event["text_key"]
            parser = handler["parser"]

            def voidtrader_factory(
                subscriber_lang: str,
                _text_key=text_key,
                _parser=parser,
                _obj=obj_new,
                _color=embed_color,
            ):
                _ts = get_ts_by_lang(subscriber_lang)
                _text_arg = _ts.get(_text_key)
                return _parser(_obj, _text_arg, _color, ts=_ts, lang=subscriber_lang)

            if event.get("have_custom_msg"):
                arg_func = handler.get("arg_func")

                def lang_arg_func(subscriber_lang: str, _af=arg_func):
                    if _af is None:
                        return None
                    _ts = get_ts_by_lang(subscriber_lang)
                    try:
                        return _af(ts=_ts, lang=subscriber_lang)
                    except TypeError:
                        return _af()

                await self.bot.broadcast_webhook(
                    origin_key,
                    content_factory=voidtrader_factory,
                    arg_func=lang_arg_func,
                )
            else:
                await self.bot.broadcast_webhook(
                    origin_key, content_factory=voidtrader_factory
                )
        # broadcast already done above; True = save voidtrader data
        return None, True

    async def _handle_deep_archimedea(
        self, handler, origin_key, key, obj_prev, obj_new
    ):
        obj_deep, is_new = handleDeepArchimedea(obj_new)
        if not is_new:
            return None
        try:
            await setDeepArchimedea(obj_deep)
        except Exception as e:
            msg = f"parse error in handle_deep_archimedea {handler['parser']}/{e}"
            await handleParseError(self.bot.db, msg, key)
            return None
        factory = _make_factory(handler["parser"], obj_deep)
        return factory, True

    async def _handle_temporal_archimedea(
        self, handler, origin_key, key, obj_prev, obj_new
    ):
        obj_temporal, is_new = handleTemporalArchimedea(obj_new)
        if not is_new:
            return None
        try:
            await setTemporalArchimedea(obj_temporal)
        except Exception as e:
            msg = f"parse error in handle_temporal_archimedea {handler['parser']}/{e}"
            await handleParseError(self.bot.db, msg, key)
            return None
        factory = _make_factory(handler["parser"], obj_temporal)
        return factory, True

    async def _handle_no_args(self, handler, origin_key, key, obj_prev, obj_new):
        if not handler["update_check"]():
            return None
        factory = _make_factory(handler["parser"])
        return factory, False

    async def _handle_bounty(self, handler, origin_key, key, obj_prev, obj_new):
        obj_bounty, is_new = await handleNewBounty(self.bot.db)
        if not obj_bounty:
            await handleParseError(self.bot.db, "error with bounty object", key)
            return None
        if not is_new:
            return None
        await set_obj_async(obj_bounty, key)
        factory = _make_factory(handler["parser"], obj_bounty)
        # already saved above (obj_bounty differs from outer obj_new)
        return factory, False

    async def _handle_default(self, handler, origin_key, key, obj_prev, obj_new):
        if not handler["update_check"](obj_prev, obj_new):
            return None
        factory = await self._safe_parse(handler, key, obj_new)
        # save even if parse failed, to keep cache in sync (matches original behavior)
        return factory, True

    # --- cog lifecycle ---

    async def cog_load(self):
        if not self.check_new_content.is_running():
            self.check_new_content.start()
            print(
                f"{C.blue}[{LOG_TYPE.info}] {C.green}{ts.get('start.crt-each')}",
                "check_new_content",
            )

    async def cog_unload(self):
        self.check_new_content.cancel()

    # auto api request & check new contents
    @tasks.loop(minutes=5.0)
    async def check_new_content(self) -> None:
        latest_data: requests.Response | None = await API_Request(self.bot.db)
        if not latest_data or latest_data.status_code != 200:
            return
        latest_data = latest_data.json()

        # pre-load all required api_cache files in parallel
        keys_to_preload = set()
        for _origin_key, _handler in DATA_HANDLERS.items():
            if _handler.get("special_logic") not in [LOGIC.no_args, LOGIC.bounty]:
                keys_to_preload.add(_handler.get("key", _origin_key))
        keys_list = list(keys_to_preload)
        loaded = await asyncio.gather(*[get_obj_async(k) for k in keys_list])
        prev_cache = dict(zip(keys_list, loaded))

        # check for new content & send alert
        for key, handler in DATA_HANDLERS.items():
            origin_key = key
            special_key = handler.get("key")
            if special_key:
                key = special_key

            special_logic = handler.get("special_logic")
            obj_prev, obj_new = None, None
            if special_logic not in [LOGIC.no_args, LOGIC.bounty]:
                try:
                    obj_prev = prev_cache.get(key)
                    obj_new = latest_data[key]
                except Exception as e:
                    msg = f"Error with loading original data (from check_new_content/DATA_HANDLERS for loop){e}"
                    await handleParseError(self.bot.db, msg, key)
                    continue

            handle_fn = self._dispatch.get(special_logic, self._handle_default)
            # noinspection PyArgumentList
            result = await handle_fn(handler, origin_key, key, obj_prev, obj_new)
            if result is None:
                continue

            content_factory, should_save = result
            if should_save:
                await set_obj_async(obj_new, key)

            if content_factory and SETTINGS["noti"]["list"][origin_key]:
                arg_func = handler.get("arg_func")
                # wrap arg_func to accept lang parameter
                lang_arg_func = None
                if arg_func:

                    def lang_arg_func(subscriber_lang: str, _af=arg_func):
                        _ts = get_ts_by_lang(subscriber_lang)
                        try:
                            return _af(ts=_ts, lang=subscriber_lang)
                        except TypeError:
                            return _af()

                await self.bot.broadcast_webhook(
                    origin_key,
                    content_factory=content_factory,
                    arg_func=lang_arg_func,
                )


async def setup(bot):
    await bot.add_cog(TASKcheck_new_content(bot))
