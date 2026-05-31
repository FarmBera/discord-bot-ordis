import discord
import orjson

from config.TOKEN import base_url_bounty, BOUNTY_JSON_PATH
from src.constants.keys import BOUNTY
from src.translator import ts as _ts, language as _default_lang
from src.utils.api_request import API_Request
from src.utils.data_manager import (
    getLanguage,
    getSolNodeData,
)
from src.utils.return_err import err_embed
from src.utils.times import convert_remain
from src.utils.data_manager import get_obj_async

pf: str = "cmd.bounty."


async def handleNewBounty(pool):
    prev: dict = await get_obj_async(BOUNTY)
    new = await API_Request(pool, base_url_bounty, BOUNTY_JSON_PATH)

    # parse object
    try:
        new = orjson.loads(new.content)
    except Exception:
        print("bounty JSON parse error!")
        return None, False

    # check object
    if not prev or not new:
        return None, False

    if prev.get("rot") == new.get("rot"):
        return new, False

    return new, True


def generateBounty(bounty, b_key, lang=_default_lang):
    output = ""
    for i in bounty[b_key]:
        node = getSolNodeData(i["node"], lang)
        output += f"- **{node['type']}** - {getLanguage(i['challenge'],lang=lang)}\n"
    return output


def w_bounty(bounty, ts=_ts, lang=_default_lang) -> discord.Embed:
    """
    parse bounty data (zariman & entrati)

    :param bounty: bounty data
    :return: parsed bounty data & img file name
    """
    if not bounty:
        return err_embed("bounty")

    output_msg: str = ts.get(f"{pf}expiry").format(
        time=convert_remain(bounty["expiry"])
    )
    bty = bounty["bounties"]

    output_msg += ts.get(f"{pf}title-z")
    output_msg += generateBounty(bty, "ZarimanSyndicate", lang)

    output_msg += ts.get(f"{pf}title-e")
    output_msg += generateBounty(bty, "EntratiLabSyndicate", lang)

    embed = discord.Embed(description=output_msg, color=discord.Color.darker_grey())
    # embed.set_thumbnail(url="attachment://i.webp")
    return embed


# print(w_bounty(get_obj(BOUNTY)).description)
