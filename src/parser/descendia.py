import discord

from config.config import Lang
from src.translator import Translator, ts as _ts, language as _default_lang
from src.utils.file_io import json_load
from src.utils.return_err import err_embed
from src.utils.times import timeNow, convert_remain

descendiaLanguage: dict = {
    Lang.EN: json_load(f"data/{Lang.EN}/descendiaLanguages.json"),
    Lang.KO: json_load(f"data/{Lang.KO}/descendiaLanguages.json"),
}
pf: str = "cmd.descendia."
format_string = "%Y-%m-%d %H:%M:%S"


def getDescendiaChallenge(challenge: str, lang: str) -> str:
    return (
        descendiaLanguage.get(lang, descendiaLanguage[Lang.EN])
        .get("challenge", {})
        .get(challenge, {})
        .get("name", "{}")
    )


def getDescendiaMiss(mission: str, lang: str) -> str:
    return (
        descendiaLanguage.get(lang, descendiaLanguage[Lang.EN])
        .get("missionType", {})
        .get(mission, {})
        .get("name", mission)
    )


def w_descendia(
    descendia, ts: Translator = _ts, lang: str = _default_lang
) -> tuple[discord.Embed, str]:
    if not descendia:
        return err_embed("descendia"), ""

    this_week_content = None
    this_week_index: int = 0
    expiry_time_int: int = 0

    # find this week's descendia challenges
    for item in descendia:
        activation_time: int = int(item["Activation"]["$date"]["$numberLong"][:10])
        expiry_time: int = int(item["Expiry"]["$date"]["$numberLong"][:10])
        if activation_time <= timeNow() <= expiry_time:
            this_week_content = item
            expiry_time_int = expiry_time if expiry_time else 0
            break

        this_week_index += 1

    if not this_week_content:
        return err_embed("ERROR: Descendia Content Not Found"), ""

    # generate output msg
    output_msg = ts.get(f"{pf}title")
    if expiry_time_int:
        output_msg += ts.get(f"{pf}remain").format(time=convert_remain(expiry_time_int))

    for challenge in descendia[this_week_index]["Challenges"]:
        output_msg += f"{challenge['Index']:2d}. {getDescendiaMiss(challenge['Type'], lang)}: {getDescendiaChallenge(challenge['Challenge'], lang)}\n"

    embed = discord.Embed(description=output_msg, color=0x883F0A)
    embed.set_thumbnail(url="attachment://i.webp")
    return embed, "descendia"


# from src.constants.keys import DESCENDIA
# from src.utils.data_manager import get_obj
# print(w_descendia(get_obj(DESCENDIA))[0].description)
