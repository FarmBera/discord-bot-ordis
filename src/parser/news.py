import discord

from config.config import Lang
from src.translator import ts as _ts, language as _default_lang
from src.utils.data_manager import getLanguage
from src.utils.return_err import err_embed

pf: str = "cmd.news."


class News:
    def __init__(self, nid, date, title, url, img):
        self.id = nid
        self.date = date
        self.title = title
        self.url = url
        self.img = img


def w_news(newses, ts=_ts, lang=_default_lang):
    if not newses:
        return err_embed("news")

    output_msg: str = f"# {ts.get(f'{pf}title')}\n"
    game_news = []
    community_news = []

    # categorize news
    for item in newses:
        t_id = item["_id"]
        try:
            t_date = int(item["Date"]["$date"]["$numberLong"])
        except:
            t_date = ""

        t_url = item["Prop"].replace(" ", "")
        if not t_url:
            if not item.get("Links"):
                t_url = ""
            elif item["Links"]:
                t_url = str(item["Links"][0]["Link"]).replace(" ", "")

        t_img = item.get("ImageUrl")

        for t_title in item["Messages"]:
            if item.get("Community") and t_title["LanguageCode"] == Lang.EN:
                t_title = getLanguage(t_title["Message"])
                community_news.append(
                    News(nid=t_id, date=t_date, title=t_title, url=t_url, img=t_img)
                )
                continue

            if t_title["LanguageCode"] == lang:
                t_title = getLanguage(t_title["Message"])
                game_news.append(
                    News(nid=t_id, date=t_date, title=t_title, url=t_url, img=t_img)
                )

    # reverse list
    game_news = game_news[::-1]
    community_news = community_news[::-1]

    # create news text
    if game_news:
        output_msg += f"## {ts.get(f'{pf}ingame')}\n"
        for item in game_news:
            output_msg += f"- [{item.title}]({item.url})\n"
    if community_news:
        output_msg += f"## {ts.get(f'{pf}comu')}\n"
        for item in community_news:
            output_msg += f"- [{item.title}]({item.url})\n"

    # create discord embed
    embed = discord.Embed(
        description=output_msg,
        color=discord.Color.darker_grey(),
    )
    # set embed thumbnail img
    img_url = None
    if game_news:
        img_url = game_news[0].img
    elif community_news:
        img_url = community_news[0].img
    if img_url:
        embed.set_image(url=img_url)

    return embed


# from src.utils.data_manager import get_obj
# from src.constants.keys import NEWS
# print(w_news(get_obj(NEWS)).description)
