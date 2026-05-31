import discord
import orjson

from config.TOKEN import base_url_market_image
from config.config import Lang, LOG_TYPE
from src.constants.keys import MSG_BOT
from src.translator import Translator, ts as _default_ts, language as _default_lang
from src.utils.api_request import API_MarketSearch
from src.utils.file_io import json_load
from src.utils.logging_utils import save_log

THRESHOLD: int = 7
SLUGS: list = json_load("data/market-item-list.json")["data"]

# pre-build per-language item name lists
_all_market_item_names: dict[str, list[str]] = {
    Lang.EN: sorted([item["i18n"][Lang.EN]["name"] for item in SLUGS]),
    Lang.KO: sorted([item["i18n"][Lang.KO]["name"] for item in SLUGS]),
}

# backward-compat: default language list
_market_item_names = _all_market_item_names.get(
    _default_lang, _all_market_item_names[Lang.EN]
)

pf: str = "cmd.market-search."


def get_market_item_names(lang: str = _default_lang) -> list[str]:
    return _all_market_item_names.get(lang, _all_market_item_names[Lang.EN])


def get_slug_data(name, lang: str = _default_lang) -> tuple[bool, str, str, str]:
    item_names = get_market_item_names(lang)

    if name not in item_names:
        # rename input name
        iname: list = []
        for item in name.split(" "):
            # en pattern
            if item in ["p", "pr", "pri", "prim"]:
                iname.append("prime")
            elif item in ["c", "ch", "cha", "chas", "chass", "chassi"]:
                iname.append("chassis")
            elif item in ["s", "sy", "sys", "syst"]:
                iname.append("systems")
            elif item in ["n", "ne", "neu", "neur", "neuro", "neurop"]:
                iname.append("neuroptics")
            elif item in ["b", "bl", "bp", "blue", "bluep"]:
                iname.append("blueprint")

            # pattern not found
            else:
                iname.append(item)

        item_slug: str = " ".join(iname)
    else:
        item_slug = name

    # find slug data
    flag: bool = False
    item_name: str = ""
    item_img_url: str = ""
    for i in SLUGS:
        if item_slug == i["i18n"][lang]["name"]:
            item_slug = i["slug"]
            item_name = i["i18n"][lang]["name"]
            item_img_url = i["i18n"][lang]["icon"]
            flag = True
            break

    return flag, item_slug, item_name, item_img_url


def categorize(result, rank: int) -> list:
    # categorize only 'ingame' stocks (ignores online, offline)
    ingame_orders: list = []

    # if rank exists: categorize only selected rank
    if rank and (0 <= rank <= 5) and result["data"][0].get("rank"):
        for item in result["data"]:
            if item["user"]["status"] != "ingame":
                continue
            if item["type"] != "sell":
                continue
            if item["rank"] != rank:
                continue
            ingame_orders.append(item)

    else:
        for item in result["data"]:
            if item["user"]["status"] != "ingame":
                continue
            if item["type"] != "sell":
                continue
            ingame_orders.append(item)

    return sorted(ingame_orders, key=lambda x: x["platinum"])


def create_market_url(name, slug=None, is_markdown=True, lang: str = _default_lang):
    msg = ""
    if is_markdown:
        msg += f"[{name}]("

    msg += f"https://warframe.market"
    msg += f"/{lang}" if lang != Lang.EN else ""

    if not slug:
        slug = get_slug_data(name, lang=lang)[1]

    msg += f"/items/{slug}?type=sell"
    if is_markdown:
        msg += ")"

    return msg


class MarketBtn(discord.ui.View):
    def __init__(
        self, name, slug, ts: Translator = _default_ts, lang: str = _default_lang
    ):
        super().__init__(timeout=None)

        self.add_item(
            discord.ui.Button(
                label=ts.get(f"{pf}shortcut"),
                url=create_market_url(name, slug, False, lang=lang),
            )
        )


async def w_market_search(
    pool,
    arg_obj: tuple[str, int],
    ts: Translator = _default_ts,
    lang: str = _default_lang,
) -> tuple[discord.Embed, discord.ui.View | None]:
    name, rank = arg_obj
    flag, item_slug, item_name, item_img_url = get_slug_data(name, lang=lang)

    if not flag:  # data not found
        return (
            discord.Embed(
                description=ts.get(f"{pf}no-result", name=name),
                color=0xE67E22,  # discord.Color.orange
            ),
            None,
        )

    # api request
    result = await API_MarketSearch(pool, item_name=item_slug)

    # check response code
    try:
        if result.status_code == 404:  # item not found
            await save_log(
                pool=pool,
                type=LOG_TYPE.api,
                cmd="w_market_search()",
                user=MSG_BOT,
                msg=f"{name},{item_slug} > 404 Not Found",
                obj=result.status_code,
            )
            return (
                discord.Embed(
                    description=ts.get(f"{pf}no-result", name=name),
                    color=0xE67E22,
                ),
                None,
            )
        elif 500 <= result.status_code == 599:  # internal server err
            await save_log(
                pool=pool,
                type=LOG_TYPE.api,
                cmd="w_market_search()",
                user=MSG_BOT,
                msg=f"{name},{item_slug} > 500 Internal Server Error",
                obj=result.status_code,
            )
            return (
                discord.Embed(description=ts.get(f"{pf}server-err"), color=0xE67E22),
                None,
            )
        elif result.status_code != 200:  # another code err
            await save_log(
                pool=pool,
                type=LOG_TYPE.api,
                cmd="w_market_search()",
                user=MSG_BOT,
                msg=f"{name},{item_slug} > {result.status_code}",
                obj=result.status_code,
            )
            return discord.Embed(description=ts.get(f"{pf}err"), color=0xE67E22), None
    except Exception as e:
        await save_log(
            pool=pool,
            type=LOG_TYPE.api,
            cmd="w_market_search()",
            user=MSG_BOT,
            msg=f"response ERROR",
            obj=str(e),
        )
        return discord.Embed(description=ts.get(f"{pf}err"), color=0xE67E22), None

    # init categorize
    ingame_orders = categorize(orjson.loads(result.content), rank=rank)
    if not ingame_orders:
        return (
            discord.Embed(
                description=ts.get(f"{pf}no-item", name=item_name),
                color=0xE67E22,
            ),
            None,
        )

    output_msg = ""

    # create output msg
    idx: int = 0
    # title
    output_msg += ts.get(
        f"{pf}result", link=create_market_url(name=item_name, slug=item_slug, lang=lang)
    )
    # item rank if exists
    output_msg += ts.get(f"{pf}rank", rank=rank) if ingame_orders[0].get("rank") else ""
    # sub desc
    output_msg += "\n"
    # item list
    for item in ingame_orders:
        idx += 1
        if idx > THRESHOLD:
            break

        output_msg += f"- **{item['platinum']} {ts.get(f'{pf}platinum')}** : {item['quantity']} {ts.get(f'{pf}qty')} (`{item['user']['ingameName']}`)\n"

    embed = discord.Embed(description=output_msg, color=0x3498DB)
    # discord.Color.blue,
    embed.set_thumbnail(url=f"{base_url_market_image}{item_img_url}")
    return embed, MarketBtn(item_name, item_slug, ts=ts, lang=lang)
