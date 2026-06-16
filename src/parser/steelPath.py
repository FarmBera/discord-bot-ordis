import datetime as dt

import discord

from src.constants.keys import FIELD_PATTERN as pat
from src.parser.worldstate import weekly_remain
from src.translator import Translator, ts as _ts, language as _default_lang
from src.utils.emoji import get_emoji
from src.utils.return_err import err_embed

SEED_TIME: str = "2026-02-02T09:00:00+09:00"
SECONDS_PER_ITEM: int = 604800
color_list: dict = {
    "Umbra Forma Blueprint": 0x00FFFF,
    "50,000 Kuva": 0xB02121,
    "3x Forma": 0xFBFF24,
    "30,000 Endo": 0xFBFF24,
    "Kitgun Riven Mod": 0xA11EE3,
    "Zaw Riven Mod": 0xA11EE3,
    "Rifle Riven Mod": 0xA11EE3,
    "Shotgun Riven Mod": 0xA11EE3,
}
img_list: dict = {
    "Umbra Forma Blueprint": "umbra-forma",
    "50,000 Kuva": "kuva",
    "3x Forma": "forma",
    "30,000 Endo": "endo",
}
LENGTH: int = len(color_list.keys())
pf: str = "cmd.steel-path-reward."


def get_thisweek_index() -> int:
    """Returns this week's item index by the current system time"""
    seed_dt = dt.datetime.fromisoformat(SEED_TIME).timestamp()
    target_dt = dt.datetime.now(dt.timezone.utc).timestamp()
    elapsed_seconds = target_dt - seed_dt  # calculate diff
    # calculate cycled index
    intervals_passed = int(elapsed_seconds // SECONDS_PER_ITEM)
    return intervals_passed % LENGTH


def w_steelPath(
    steel, ts: Translator = _ts, lang: str = _default_lang
) -> tuple[discord.Embed, str]:
    if not steel:
        return err_embed(ts.get("err.steelpath-not-found")), ""

    curr_idx: int = get_thisweek_index()
    stl = steel["rotation"]
    length: int = len(stl)

    # current item
    current_reward_item = stl[curr_idx]
    cname: str = current_reward_item["name"]

    output_msg = ts.get(f"{pf}output").format(timer=weekly_remain())

    # text layout
    for i in range(length):
        target_item = stl[i]
        origin_name = target_item["name"]
        name = f"{get_emoji(origin_name)} {ts.trs(origin_name)}"
        # cost = f"{target_item['cost']}x {get_emoji('steel-essense')}"

        # this week item
        if i == curr_idx:
            output_msg += f"{i+1}. __**{ts.get(f'{pf}current')}**__: __**{name}**__\n"
            # output_msg += f"(__**{cost}**__)\n"
        else:
            if i > curr_idx:
                delta = i - curr_idx
            else:
                delta = length - curr_idx + i
            delta -= 1

            output_msg += f"{i+1}. {weekly_remain(delta)}: {name}\n"
            # output_msg += f" ({cost})\n"

    embed = discord.Embed(
        description=output_msg.strip(),
        colour=color_list.get(cname, discord.Color.darker_grey()),
    )
    embed.set_thumbnail(url="attachment://i.webp")
    return embed, img_list.get(cname, "riven-mod")

    # # table layout
    # weeks: list = []
    # items: list = []
    # costs: list = []
    # for i in range(length):
    #     target_item = stl[i]
    #     origin_name = target_item["name"]
    #     name = f"{get_emoji(origin_name)} {ts.trs(origin_name)}"
    #     cost = f"{target_item['cost']}x {get_emoji('essense')}"
    #
    #     # this week item
    #     if i == curr_idx:
    #         weeks.append(f"__**{ts.get(f'{pf}current')}**__")
    #         items.append(f"__**{name}**__")
    #         costs.append(f"__**{cost}**__")
    #     else:
    #         if i > curr_idx:
    #             delta = i - curr_idx
    #         else:
    #             delta = length - curr_idx + i
    #         delta -= 1
    #
    #         weeks.append(weekly_remain(delta))
    #         items.append(name)
    #         costs.append(cost)
    #
    # embed = discord.Embed(
    #     description=output_msg.strip(),
    #     colour=color_list.get(cname, discord.Color.darker_grey()),
    # )
    # embed.set_thumbnail(url="attachment://i.webp")
    # embed.add_field(name=ts.get(f"{pf}week"), value=pat.join(weeks), inline=True)
    # embed.add_field(name=ts.get(f"{pf}item"), value=pat.join(items), inline=True)
    # embed.add_field(name=ts.get(f"{pf}cost"), value=pat.join(costs), inline=True)
    # return embed, img_list.get(cname, "riven-mod")


# from src.utils.data_manager import get_obj
# from src.constants.keys import STEELPATH
# d: tuple[discord.Embed, str] = w_steelPath(get_obj(STEELPATH))
# print(d[0].description)
# print(d[0].fields[1].value, d[1], sep="\n")
