import datetime as dt

import discord

from src.constants.keys import FIELD_PATTERN as pat
from src.parser.cambionCycle import CambionCycleData
from src.parser.cetusCycle import CetusTimerData
from src.parser.duviriCycle import duviri_cycle
from src.parser.vallisCycle import VallisCycleData
from src.translator import Translator, ts as _ts, language as _default_lang
from src.utils.emoji import worldstate_emoji
from src.utils.return_err import err_embed
from src.utils.times import check_timer_states, convert_remain

pf: str = "cmd.worldstate."


class WeeklyTimerData:
    name = "Weekly Reset Timer"
    start_date = dt.datetime(2024, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc)
    looptime = 604800
    delaytime = 0
    beforetext = _ts.get(f"{pf}expiry")
    aftertext = "before reset"


def weekly_remain(delta: int = 0) -> str:
    return check_timer_states(WeeklyTimerData, delta=delta)["time_left"]


def w_worldstate(
    ts: Translator = _ts, lang: str = _default_lang
) -> tuple[discord.Embed, str]:
    try:
        cetus = check_timer_states(CetusTimerData)
        duviri = duviri_cycle.current()
        cambion = check_timer_states(CambionCycleData)
        vallis = check_timer_states(VallisCycleData)
        if not cetus or not duviri or not cambion or not vallis:
            raise ValueError("ERROR FETCHING DATA")
    except Exception:
        return err_embed(ts.get("err.worldstate-fetch-failed")), ""

    title: str = ts.get(f"{pf}title")

    worlds = ts.get(f"{pf}world_names")
    states = [
        f"{worldstate_emoji[cetus['current']]} {ts.get(f'cmd.cetus.{cetus['current']}')}",
        f"{worldstate_emoji[duviri.state.label]} {ts.get(f'cmd.duviri-cycle.{duviri.state.label}')}",
        f"{worldstate_emoji[cambion['current']]} {ts.get(f'cmd.cambion.{cambion['current']}')}",
        f"{worldstate_emoji[vallis['current']]} {ts.get(f'cmd.vallis.{vallis['current']}')}",
    ]
    expiry = [
        cetus["time_left"],
        convert_remain(duviri.expires_at),
        cambion["time_left"],
        vallis["time_left"],
    ]

    embed = discord.Embed(description=title, color=discord.Color.darker_grey())
    embed.add_field(name=ts.get(f"{pf}world"), value=pat.join(worlds), inline=True)
    embed.add_field(name=ts.get(f"{pf}state"), value=pat.join(states), inline=True)
    embed.add_field(name=ts.get(f"{pf}expiry"), value=pat.join(expiry), inline=True)
    embed.set_thumbnail(url="attachment://i.webp")
    return embed, "worldstate"


# print(w_worldstate()[0].fields)
