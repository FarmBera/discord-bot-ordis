import discord

from src.translator import ts as _ts, language as _default_lang
from src.utils.data_manager import getLanguage, getMissionType, getSolNode
from src.utils.emoji import get_emoji
from src.utils.times import convert_remain

pf: str = "cmd.events."


def color_decision(t):
    return 0x4DD2FF if t else 0xFFA826


def w_events(events, ts=_ts, lang=_default_lang) -> discord.Embed:
    if not events:  # empty list
        return discord.Embed(
            description=ts.get(f"{pf}desc-none"), color=color_decision(events)
        )

    output_msg: str = f"{ts.get(f'{pf}title').format(count=len(events))}\n"

    idx: int = 0
    for e in events:
        idx += 1
        # event title
        output_msg += f"## {idx}. {getLanguage(e['Desc'], lang=lang)}\n"
        # desc
        # output_msg += f"- {getLanguage(e['ToolTip'])}\n"
        # status percent
        if e.get("HealthPct"):
            output_msg += (
                ts.get(f"{pf}process").format(perc=f"{(e['HealthPct'] * 100):.1f}")
                + "\n"
            )
        # expiry
        output_msg += f"{ts.get(f'{pf}exp').format(time=convert_remain(e['Expiry']['$date']['$numberLong']))}\n"
        # mission info
        if e.get("MissionInfo"):
            ee = e["MissionInfo"]
            output_msg += f"""{ts.get(f'{pf}miss-title')}
{ts.get(f'{pf}miss-info').format(type=getMissionType(ee['missionType'], lang), loc=getSolNode(ee['location'], lang), min=ee['minEnemyLevel'], max=ee['maxEnemyLevel'])}
"""
            # required items
            if ee.get("requiredItems"):
                output_msg += (
                    "- "
                    + ts.get(f"{pf}require-item").format(
                        ilist=", ".join(
                            getLanguage(i, lang=lang) for i in ee["requiredItems"]
                        )
                    )
                    + "\n"
                )
        # rewards title
        output_msg += ts.get(f"{pf}reward-title")
        has_interim: bool = e.get("InterimGoals") and e.get("InterimRewards")
        # rewards list
        if has_interim:
            for i in range(len(e.get("InterimGoals"))):
                output_msg += f"- {e['InterimGoals'][i]}% : {", ".join([getLanguage(item, lang=lang) for item in e['InterimRewards'][i]['items'] ])}\n"
        # final rewards
        if e.get("Reward"):
            output_msg += "- 100% : " if has_interim else "- "
            # credit
            output_msg += (
                f"{e['Reward']['credits']:,} {get_emoji('credit')}, "
                if e["Reward"].get("credits")
                else ""
            )
            # other items
            output_msg += ", ".join(
                [
                    f"{getLanguage(i, lang=lang)} {get_emoji(getLanguage(i, lang=lang))}"
                    for i in e["Reward"]["items"]
                ]
            )
        output_msg += "\n"

    embed = discord.Embed(
        description=output_msg,
        color=0x00FFFF,
    )
    # set embed thumb
    # img_url = None
    # if img_url:
    #     embed.set_image(url=img_url)

    return embed


# from src.constants.keys import EVENTS
# from src.utils.data_manager import get_obj
# print(w_events(get_obj(EVENTS)).description)
