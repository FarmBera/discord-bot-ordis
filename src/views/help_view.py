from discord.ui import View, Button

from config.TOKEN import HOMEPAGE, DONATION, SUPPORT_SERVER
from src.translator import ts

pf: str = "view.support-"


class SupportMasterView(View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(
            Button(label=ts.get(f"{pf}support"), url=f"{SUPPORT_SERVER}", row=1)
        )
        self.add_item(Button(label=ts.get(f"{pf}help"), url=f"{HOMEPAGE}", row=2))
        self.add_item(Button(label=ts.get(f"{pf}tos"), url=f"{HOMEPAGE}/tos", row=2))
        self.add_item(
            Button(label=ts.get(f"{pf}privacy"), url=f"{HOMEPAGE}/privacy", row=2)
        )
        self.add_item(Button(label=ts.get(f"{pf}donate"), url=DONATION, row=3))


class SupportView(View):
    def __init__(self):
        super().__init__(timeout=None)

        self.add_item(Button(label=ts.get(f"{pf}faq"), url=f"{HOMEPAGE}/faq", row=1))
        self.add_item(
            Button(label=ts.get(f"{pf}support"), url=f"{SUPPORT_SERVER}", row=1)
        )
