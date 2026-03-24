import random

import discord

from src.translator import Translator, ts as _ts, language as _default_lang
from src.utils.data_manager import getSolNode, getLanguage
from src.utils.emoji import get_emoji
from src.utils.formatter import extract_last_part, add_space, check_str_length
from src.utils.return_err import err_embed
from src.utils.times import timeNow, convert_remain

baro_img = ["baro-ki-teer", "baro"]  # VAR
pf: str = "cmd.void-traders."
pfi = "cmd.void-traders-item."

BARO_MSG: list = _ts.get(f"{pf}msg")
MSG_MAX_LENGTH: int = len(BARO_MSG) - 1


def getBaroRandomMsg() -> str:
    return f"*{BARO_MSG[random.randint(0, MSG_MAX_LENGTH)]}*\n"


def getBaroImg(name: str = "") -> str:
    if name and "evil" in name.lower():
        return "baro-evil"
    return baro_img[random.randrange(0, len(baro_img))]


def isBaroActive(act: int, exp: int) -> bool:
    curr: int = timeNow()

    t_list = [act, exp]

    for i in range(2):
        ts_str = str(t_list[i])
        # conert milliseconds to seconds
        if len(ts_str) == 13:
            t_list[i] = int(ts_str) / 1000
        else:
            t_list[i] = int(ts_str)

    active, expiry = t_list
    return True if active < curr < expiry else False


def color_decision(active_flag):
    if active_flag:
        return 0x4DD2FF
    return 0xFFA826


def w_voidTraders(
    trader,
    text_arg=None,
    embed_color=None,
    ts: Translator = _ts,
    lang: str = _default_lang,
) -> tuple:
    active_flag: bool = False

    if not trader:
        return "", err_embed(ts.get("err.void-traders-not-found"))

    idx = 1
    length: int = len(trader)
    output_msg: str = ""

    for td in trader:
        t_act: int = int(td["Activation"]["$date"]["$numberLong"])
        t_exp: int = int(td["Expiry"]["$date"]["$numberLong"])
        baro_active = isBaroActive(t_act, t_exp)

        if baro_active:
            active_flag = True

        # title
        output_msg += "# {idx}{msg}\n".format(
            idx=f"{idx}. " if length >= 2 else "",
            msg=text_arg if text_arg else ts.get(f"{pf}title"),
        )
        # body
        output_msg += ts.get(f"{pf}embed-body").format(
            trader=ts.trs(td["Character"]),
            status=(
                f"✅ **{ts.get(f'{pf}activate')}**"
                if baro_active
                else f"❌ *{ts.get(f'{pf}deactivate')}*"
            ),
            time=ts.get(f"{pf}time-format").format(
                text=ts.get(f"{pf}leave") if baro_active else ts.get(f"{pf}appear"),
                time=convert_remain(t_exp) if baro_active else convert_remain(t_act),
            ),
            location=getSolNode(td["Node"], lang),
        )

    embed = discord.Embed(
        description=output_msg.strip(),
        color=embed_color if embed_color else color_decision(active_flag),
    )
    embed.set_thumbnail(url="attachment://i.webp")
    return embed, getBaroImg(trader[0]["Character"])


def w_voidTradersItem(
    trader, ts: Translator = _ts, lang: str = _default_lang
) -> discord.Embed:
    if not trader:
        return err_embed(ts.get("err.void-traders-not-found"))

    active_flag_item: bool = False
    output_msg: str = ""

    for td in trader:
        list_item: list = []

        if not td.get("Manifest", []):
            list_item.append(
                f"{ts.get(f'{pfi}not-yet').format(time=convert_remain(td['Activation']['$date']['$numberLong']))}"
            )
        else:
            active_flag_item = True

        for jtem in td.get("Manifest", []):
            k: str = jtem["ItemType"].replace("/Lotus/StoreItems", "").lower()

            if "/mods/" in k:
                itype = ts.get(f"{pfi}mods")
            elif "/skins/" in k:
                itype = ts.get(f"{pfi}skin")
            elif "/shipdecos/" in k:
                itype = ts.get(f"{pfi}deco")
            elif "/weapons/" in k:
                itype = ts.get(f"{pfi}weapon")
            elif "/boosters/" in k:
                itype = ts.get(f"{pfi}booster")
            elif "/avatarimages/" in k:
                itype = ts.get(f"{pfi}glyph")
            elif "/songitems/" in k:
                itype = ts.get(f"{pfi}music")
            elif "/projections/" in k:
                itype = ts.get(f"{pfi}relic")
            elif "/keys/" in k:
                itype = ts.get(f"{pfi}keys")
            else:
                itype = ts.get(f"{pfi}other")

            iname = getLanguage(jtem["ItemType"], lang=lang)
            if "/lotus" in iname.lower():
                iname = f"__{add_space(extract_last_part(iname))}__"

            out = f"{itype} / {iname} / {jtem['PrimePrice']} {get_emoji('ducat')} {int((jtem['RegularPrice'])):,} {get_emoji('credit')}"
            list_item.append(out)

        list_item.sort()

        output_msg += (
            f"# {ts.trs(td['Character'])} at {getSolNode(td['Node'], lang)}\n\n"
        )
        for jtem in list_item:
            output_msg += f"- {jtem}\n"
        output_msg += "\n"

    return discord.Embed(
        description=check_str_length(output_msg), color=color_decision(active_flag_item)
    )


# from src.utils.data_manager import get_obj
# from src.constants.keys import VOIDTRADERS
# print(w_voidTraders(get_obj(VOIDTRADERS))[0].description)
# print(w_voidTradersItem(get_obj(VOIDTRADERS)).description)
