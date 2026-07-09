import discord

from src.translator import ts as _ts, language as _default_lang
from src.utils.data_manager import getLanguage
from src.utils.return_err import err_embed

pf: str = "cmd.seasoninfo."


def w_nightwave(season, ts=_ts, lang=_default_lang) -> tuple[discord.Embed, str]:
    """
    parse nightwave data

    :param season: nightwave data (SeasonInfo)
    :return: parsed nightwave data & img file name
    """
    if not season:
        return err_embed("nightwave object missing"), ""

    daily: list = []
    weekly: list = []

    output_msg: str = ts.get(f"{pf}title")
    preset: str = "- {type}**{value}**: {desc}\n"

    for item in season["ActiveChallenges"]:
        challenge = item["Challenge"]
        output = preset.format(
            type=f'[{ts.get(f"{pf}dd")}] ' if "/daily/" in challenge.lower() else "",
            value=getLanguage(challenge, "value", lang),
            desc=getLanguage(challenge, "desc", lang),
        )

        if "/daily/" in challenge.lower():
            daily.append(output)
        else:
            weekly.append(output)

    # create output message
    output_msg += "".join(daily) + "".join(weekly)

    # # divide daily/weekly heading
    # if daily:
    #     output_msg += ts.get(f"{pf}daily").format(daily="".join(daily).strip())
    # if weekly:
    #     output_msg += ts.get(f"{pf}weekly").format(weekly="".join(weekly).strip())

    embed = discord.Embed(
        description=output_msg.strip(), color=discord.Color.darker_grey()
    )
    embed.set_thumbnail(url="attachment://i.webp")
    return embed, "nightwave"


# from src.constants.keys import SEASONINFO
# from src.utils.data_manager import get_obj
# print(w_nightwave(get_obj(SEASONINFO))[0].description)
