import discord

from src.translator import ts as _ts, language as _default_lang
from src.utils.data_manager import getSolNodeData
from src.utils.file_io import json_load
from src.utils.image import getThumbImg
from src.utils.times import timeNow, convert_remain

ARBITRATION = json_load("data/arbys.json")

pf: str = "cmd.arbitration."


def w_arbitration(ts=_ts, lang=_default_lang) -> discord.Embed:
    cnt: int = 0  # count
    curr_arbi: dict = {}
    current: int = timeNow()

    # search current data
    for item in ARBITRATION:
        if item["time"] > current:
            curr_arbi = ARBITRATION[cnt - 1]
            break
        cnt += 1

    next_arbi = ARBITRATION[cnt]
    curr_arbi = getSolNodeData(curr_arbi["node"], lang)

    # current mission
    output_msg: str = ts.get(f"{pf}output").format(
        miss=curr_arbi["type"],
        node=curr_arbi["value"],
        faction=curr_arbi["enemy"],
        time=convert_remain(next_arbi["time"]),
    )
    # next missions
    output_msg = output_msg.strip()
    for i in range(cnt, cnt + 6):
        present = ARBITRATION[i]

        output_msg += ts.get(f"{pf}outnext").format(
            time=convert_remain(present["time"]),
            miss=getSolNodeData(present["node"])["type"],
        )

    embed = discord.Embed(description=output_msg, color=discord.Color.greyple())
    embed.set_thumbnail(url=getThumbImg("vitus-essence"))
    return embed


# print(w_arbitration().description)
