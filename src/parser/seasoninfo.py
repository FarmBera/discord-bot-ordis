import discord

from src.translator import ts as _ts, language as _default_lang
from src.utils.data_manager import getLanguage
from src.utils.return_err import err_embed
from src.utils.times import convert_remain

pf: str = "cmd.seasoninfo."


def w_nightwave(season, ts=_ts, lang=_default_lang) -> tuple[discord.Embed, str]:
    """
    parse nightwave data

    :param season: nightwave data (SeasonInfo)
    :return: parsed nightwave data & img file name
    """
    if not season:
        return err_embed("nightwave (seasoninfo)"), ""

    output_msg: str = ts.get(f"{pf}title")
    output_msg += ts.get(f"{pf}expiry").format(
        time=convert_remain(season["Expiry"]["$date"]["$numberLong"])
    )
    preset = ts.get(f"{pf}output")
    for chal in season["ActiveChallenges"]:
        output_msg += preset.format(
            value=getLanguage(chal["Challenge"], "value", lang),
            desc=getLanguage(chal["Challenge"], "desc", lang),
        )

    embed = discord.Embed(description=output_msg, color=discord.Color.darker_grey())
    embed.set_thumbnail(url="attachment://i.webp")
    return embed, "nightwave"


# print(w_nightwave(get_obj(SEASONINFO))[0].description)
