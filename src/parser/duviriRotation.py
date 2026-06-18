import discord

from src.constants.keys import DUVIRI_ROTATION, DUVIRI_U_K_W, DUVIRI_U_K_I, DUVIRI_CACHE
from src.parser.worldstate import weekly_remain
from src.translator import ts as _ts, language as _default_lang, Lang
from src.utils.data_manager import get_obj, set_obj_async
from src.utils.emoji import get_emoji
from src.utils.file_io import json_load_async, json_load
from src.utils.return_err import err_embed

rotation_data = json_load(DUVIRI_CACHE)
duv_warframe = get_obj(f"{DUVIRI_ROTATION}{DUVIRI_U_K_W}")
duv_incarnon = get_obj(f"{DUVIRI_ROTATION}{DUVIRI_U_K_I}")

IDX_MAX_WAF: int = len(rotation_data["warframe"])
IDX_MAX_INC: int = len(rotation_data["incarnon"])

pf: str = "cmd.duviri-circuit."


def getDuvWarframe():
    global duv_warframe
    return duv_warframe


def getDuvIncarnon():
    global duv_incarnon
    return duv_incarnon


async def setDuviriRotate():
    global rotation_data
    rotation_data = await json_load_async(DUVIRI_CACHE)


async def setDuvWarframe(obj):
    global duv_warframe
    duv_warframe = obj
    await set_obj_async(obj, f"{DUVIRI_ROTATION}{DUVIRI_U_K_W}")


async def setDuvIncarnon(obj):
    global duv_incarnon
    duv_incarnon = obj
    await set_obj_async(obj, f"{DUVIRI_ROTATION}{DUVIRI_U_K_I}")


def create_embed(
    output_msg: str, color=discord.Color.darker_grey(), lang=_default_lang
):
    embed = (
        discord.Embed(description=output_msg, color=color)
        if color
        else discord.Embed(description=output_msg)
    )
    if lang != Lang.KO:
        embed.set_thumbnail(url="attachment://i.webp")
        return embed, "zariman"
    return embed


def w_duviri_warframe(rotation, ts=_ts, lang=_default_lang) -> discord.Embed:
    if not rotation:
        return err_embed("w_duviri_warframe")

    curr_rotation = rotation[0]["CategoryChoices"][0]["Choices"]

    # title
    output_msg: str = (
        f"# {ts.get(f'{pf}wf-lvl')} {ts.get(f'{pf}circuit')} - {ts.get(f'{pf}wf-title')}\n"
    )
    # sub-title
    output_msg += f"### __{ts.get(f'{pf}curr-rotate')}__\n"
    # items
    output_msg += ", ".join(
        [f"{ts.trs(item)} {get_emoji(item)}" for item in curr_rotation]
    )
    # ends in
    output_msg += f"\n{ts.get(f'{pf}end').format(day=weekly_remain())}\n"
    # next items
    warframe_list = rotation_data["warframe"]
    length = len(warframe_list)
    if length == 0:
        return create_embed(output_msg, lang=lang)
    # init index (find curr index)
    idx, idx_init = 0, 0
    for item in warframe_list:
        if set(item) == set(curr_rotation):
            idx_init = idx
            break
        idx += 1
    # create next rotation list
    output_msg += f"### __{ts.get(f'{pf}next-rotate')}__\n"
    for i in range(length - 1):
        idx = (idx + 1) % length
        if idx == idx_init:
            break

        jtem = warframe_list[idx]
        output_msg += (
            f"{weekly_remain(i)}: "
            + ", ".join([f"{ts.trs(i)} {get_emoji(str(i))}" for i in jtem])
            + "\n"
        )
    return create_embed(output_msg, lang=lang)


def w_duviri_incarnon(incarnon, ts=_ts, lang=_default_lang) -> discord.Embed:
    if not incarnon:
        return err_embed("w_duviri_warframe")

    curr_rotation = incarnon[0]["CategoryChoices"][1]["Choices"]
    # title
    output_msg: str = (
        f"# {ts.get(f'{pf}inc-lvl')} {ts.get(f'{pf}circuit')} - {ts.get(f'{pf}inc-title')}\n"
    )
    # sub-title
    output_msg += f"### __{ts.get(f'{pf}curr-rotate')}__\n"
    # items
    output_msg += ", ".join([f"{ts.trs(i)} {get_emoji(i)}" for i in curr_rotation])
    # ends in
    output_msg += f"\n{ts.get(f'{pf}end').format(day=weekly_remain())}\n"
    # next items
    incarnon_list = rotation_data["incarnon"]
    length = len(incarnon_list)
    if length == 0:
        return create_embed(output_msg=output_msg, color=0x65E6E1, lang=lang)
    # init index (find curr index)
    idx, idx_init = 0, 0
    for item in incarnon_list:
        if set(item) == set(curr_rotation):
            idx_init = idx
            break
        idx += 1
    # create next rotation list
    output_msg += f"### __{ts.get(f'{pf}next-rotate')}__\n"
    for i in range(length - 1):
        idx = (idx + 1) % length
        if idx == idx_init:
            break

        jtem = incarnon_list[idx]
        output_msg += (
            f"{weekly_remain(i)}: "
            + ", ".join([f"{ts.trs(i)} {get_emoji(str(i))}" for i in jtem])
            + "\n"
        )
    return create_embed(output_msg=output_msg, color=0x65E6E1, lang=lang)


print(w_duviri_warframe(get_obj(f"{DUVIRI_ROTATION}")).description)
print(w_duviri_incarnon(get_obj(f"{DUVIRI_ROTATION}")).description)
