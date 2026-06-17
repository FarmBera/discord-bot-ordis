import discord
from discord import app_commands
from discord.ext import commands

from src.commands.cmd_maintenance import cmd_helper_maintenance
from src.constants.keys import (
    # cooldown var
    COOLDOWN_DEFAULT,
    COOLDOWN_5_MIN,
    # docs file
    HELP_FILE_LOC,
    ANNOUNCE_FILE_LOC,
    POLICY_FILE_LOC,
    # cmd obj
    ALERTS,
    NEWS,
    CETUSCYCLE,
    SORTIE,
    ARCHONHUNT,
    VOIDTRADERS,
    STEELPATH,
    ARCHIMEDEA,
    ARCHIMEDEA_DEEP,
    ARCHIMEDEA_TEMPORAL,
    FISSURES,
    DUVIRICYCLE,
    CALENDAR,
    CAMBIONCYCLE,
    DAILYDEALS,
    INVASIONS,
    MARKET_SEARCH,
    VALLISCYCLE,
    DUVIRI_ROTATION,
    DUVIRI_U_K_W,
    DUVIRI_U_K_I,
    EVENTS,
    DESCENDIA,
    ARBITRATION,
    WORLDSTATE,
    BOUNTY,
    SEASONINFO,
    COOLDOWN_CREATE,
)
from src.parser.marketsearch import get_market_item_names
from src.translator import ts, locale_to_lang
from src.utils.cmd_helper import cmd_helper_txt


class MaintenanceCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # help command
    @app_commands.command(name="help", description="cmd.help.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_help(
        self, interact: discord.Interaction, developer_options: bool = False
    ):
        await cmd_helper_txt(
            interact, file_name=HELP_FILE_LOC, isPrivateMsg=developer_options
        )

    # announcement command
    @app_commands.command(name="announcement", description="cmd.announcement.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_announcement(
        self, interact: discord.Interaction, developer_options: bool = False
    ):
        await cmd_helper_txt(
            interact, file_name=ANNOUNCE_FILE_LOC, isPrivateMsg=developer_options
        )

    # patch-note command
    @app_commands.command(name="patch-note", description="cmd.patch-note.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_patch_note(
        self, interact: discord.Interaction, developer_options: bool = False
    ):
        await cmd_helper_maintenance(interact, "patch-note")

    # privacy-policy command
    @app_commands.command(name="privacy-policy", description="cmd.privacy-policy.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_privacy_policy(
        self, interact: discord.Interaction, developer_options: bool = False
    ):
        await cmd_helper_txt(
            interact, file_name=POLICY_FILE_LOC, isPrivateMsg=developer_options
        )

    # news command
    @app_commands.command(name="news", description="cmd.news.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_news(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, NEWS)

    # alerts command
    @app_commands.command(name="alerts", description="cmd.alerts.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_alerts(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, ALERTS)

    # cetus command (cetusCycle)
    @app_commands.command(name="cetus", description="cmd.cetus.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_cetus(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, CETUSCYCLE)

    # sortie command
    @app_commands.command(name="sortie", description="cmd.sortie.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_sortie(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, SORTIE)

    # archon hunt command
    @app_commands.command(name="archon-hunt", description="cmd.archon-hunt.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_archon_hunt(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, ARCHONHUNT)

    # void traders command
    @app_commands.command(name="void-traders", description="cmd.void-traders.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_voidTraders(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, VOIDTRADERS)

    # steel path reward command
    @app_commands.command(
        name="steel-path-reward", description="cmd.steel-path-reward.desc"
    )
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_steel_reward(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, STEELPATH)

    # fissures command
    @app_commands.command(name="fissures", description="cmd.fissures.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    # @discord.app_commands.choices(
    #     types=[
    #         discord.app_commands.Choice(
    #             name=ts.get("cmd.fissures.choice-fast"), value=1
    #         ),
    #         # discord.app_commands.Choice(
    #         #     name=ts.get("cmd.fissures.choice-all"), value=2
    #         # ),
    #     ]
    # )
    async def cmd_fissures(
        self,
        interact: discord.Interaction,
        # types: discord.app_commands.Choice[int],
        # is_include_railjack_node: bool = False,
        developer_options: bool = True,
    ):
        await cmd_helper_maintenance(interact, FISSURES)

    # deep-archimedea command
    @app_commands.command(
        name="deep-archimedea", description="cmd.deep-archimedea.desc"
    )
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_deep_archimedea(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, f"{ARCHIMEDEA}{ARCHIMEDEA_DEEP}")

    # temporal-archimedea command
    @app_commands.command(
        name="temporal-archimedea",
        description=ts.get(f"cmd.temporal-archimedea.desc"),
    )
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_temporal_archimedea(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, f"{ARCHIMEDEA}{ARCHIMEDEA_TEMPORAL}")

    # duviriCycle command
    @app_commands.command(name="duviri-cycle", description="cmd.duviri-cycle.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_duviri_cycle(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, DUVIRICYCLE)

    # 1999 calendar
    @app_commands.command(name="calendar", description="cmd.calendar.desc")
    # @app_commands.choices(types=[app_commands.Choice(name="Prize", value=1),app_commands.Choice(name="To-Do", value=2),app_commands.Choice(name="Over", value=3)])
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_calendar(
        self,
        interact: discord.Interaction,
        # types: app_commands.Choice[int],
        developer_options: bool = True,
    ):
        await cmd_helper_maintenance(interact, CALENDAR)

    # cambion command (cambionCycle)
    @app_commands.command(name="cambion", description=f"cmd.cambion.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_cambion(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, CAMBIONCYCLE)

    # dailyDeals command
    @app_commands.command(name="dailydeals", description="cmd.dailydeals.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_dailydeals(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, DAILYDEALS)

    # invasions command
    @app_commands.command(name="invasions", description="cmd.invasions.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_invasions(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, INVASIONS)

    # voidTrader item command
    @app_commands.command(
        name="void-traders-item", description="cmd.void-traders-item.desc"
    )
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_traders_item(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, f"{VOIDTRADERS}-item")

    # search 'warframe.market' commnad
    @app_commands.command(name="market-search", description="cmd.market-search.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.describe(
        item_name="cmd.market-search.desc-item-name",
        item_rank="cmd.market-search.desc-item-rank",
    )
    async def cmd_market_search(
        self,
        interact: discord.Interaction,
        item_name: str,
        item_rank: int = None,
        developer_options: bool = True,
    ):
        await cmd_helper_maintenance(
            interact, f"{MARKET_SEARCH}//{item_name}//{item_rank}"
        )

    @cmd_market_search.autocomplete("item_name")
    async def market_search_autocomplete(
        self, interact: discord.Interaction, current: str
    ) -> list[discord.app_commands.Choice[str]]:
        """Autocompletes the item name for the market search."""
        user_lang = locale_to_lang(interact.locale)
        choices = [
            discord.app_commands.Choice(name=name, value=name)
            for name in get_market_item_names(user_lang)
            if current.lower() in name.lower()
        ]
        return choices[:25]

    # vallisCycle command
    @app_commands.command(name="vallis", description="cmd.vallis.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_vallis(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, VALLISCYCLE)

    # duviri-circuit-warframe
    @app_commands.command(
        name="duviri-wf",
        description="cmd.duviri-circuit.wf-desc",
        extras={"key": "cmd.duviri-circuit.wf-cmd"},
    )
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_circuit_wf(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, f"{DUVIRI_ROTATION}{DUVIRI_U_K_W}")

    # duviri-circuit-incarnon
    @app_commands.command(
        name="duviri-incarnon",
        description="cmd.duviri-circuit.inc-desc",
        extras={"key": "cmd.duviri-circuit.inc-cmd"},
    )
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_circuit_inc(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, f"{DUVIRI_ROTATION}{DUVIRI_U_K_I}")

    # events (like thermina, fomorian)
    @app_commands.command(name="events", description="cmd.events.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_ingame_events(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, EVENTS)

    # setup alert
    @app_commands.command(name="alert-set", description="cmd.alert-set.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def noti_subscribe(self, interact: discord.Interaction):
        await cmd_helper_maintenance(interact, "noti-set")

    @app_commands.command(name="alert-delete", description="cmd.alert-delete.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def noti_unsubscribe(self, interact: discord.Interaction):
        await cmd_helper_maintenance(interact, "noti-delete")

    @app_commands.command(name="descendia", description="cmd.descendia.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_descendia(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, DESCENDIA)

    @app_commands.command(name="complain", description=f"cmd.complain.desc")
    @discord.app_commands.checks.cooldown(
        1, COOLDOWN_5_MIN, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_receive_complain(self, interact: discord.Interaction) -> None:
        await cmd_helper_maintenance(interact, "complain")

    @app_commands.command(name="party", description="cmd.party.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_CREATE, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.describe(
        title="cmd.party.desc-title",
        game_name="cmd.party.desc-game-name",
        departure="cmd.party.desc-departure",
        descriptions="cmd.party.desc-descriptions",
        number_of_user="cmd.party.desc-number-of-user",
    )
    async def cmd_create_party(
        self,
        interact: discord.Interaction,
        title: str,
        game_name: str = "워프레임",
        departure: str = None,
        descriptions: str = ts.get(f"cmd.party.c-no-desc"),
        number_of_user: int = 4,
    ):
        await cmd_helper_maintenance(
            interact,
            f"party//{title}//{game_name}//{departure}//{descriptions}//{number_of_user} ",
        )

    @app_commands.command(name="trade", description=f"cmd.trade.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_CREATE, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.choices(
        trade_type=[
            app_commands.Choice(name=ts.get("cmd.trade.type-sell"), value=1),
            app_commands.Choice(name=ts.get("cmd.trade.type-buy"), value=2),
        ]
    )
    @app_commands.describe(
        trade_type="cmd.trade.desc-trade-type",
        item_name="cmd.trade.desc-item-name",
        item_rank="cmd.trade.desc-item-rank",
        # game_nickname="cmd.trade.desc-nickname",
        price="cmd.trade.desc-price",
        quantity="cmd.trade.desc-quantity",
    )
    async def cmd_create_trade(
        self,
        interact: discord.Interaction,
        trade_type: app_commands.Choice[int],
        item_name: str,
        # game_nickname: str = "",
        item_rank: int = 0,
        price: int = 0,
        quantity: int = 1,
    ):
        await cmd_helper_maintenance(
            interact,
            f"trade//{trade_type}//{item_name}//{item_rank}//{price}//{quantity}",
        )

    # auto complete item
    # noinspection PyUnusedLocal
    @cmd_create_trade.autocomplete("item_name")
    async def trade_item_name_autocomplete(
        self, interact: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        choices = [
            app_commands.Choice(name=name, value=name)
            for name in get_market_item_names()
            if current.lower() in name.lower()
        ]
        return choices[:25]

    # warn or ban user
    @app_commands.command(name="user-ban", description="cmd.user-ban.desc")
    @discord.app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def cmd_user_warn(
        self,
        interact: discord.Interaction,
        user: discord.Member,
    ) -> None:
        await cmd_helper_maintenance(
            interact,
            f"user-warn//{user.id}//{user.name}//{user.global_name}//{user.display_name}",
        )

    @app_commands.command(name="register", description="cmd.register.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_5_MIN, key=lambda i: (i.guild_id, i.user.id)
    )
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def register_channel(self, interact: discord.Interaction):
        await cmd_helper_maintenance(interact, "register")

    @app_commands.command(
        name="steel-incursion", description="cmd.steel-incursion.desc"
    )
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_steelpath_incursions(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, f"{STEELPATH}-incursion")

    @app_commands.command(name="arbitration", description="cmd.arbitration.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_arbitration(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, ARBITRATION)

    @app_commands.command(name="worldstate", description="cmd.worldstate.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_worldstate(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, WORLDSTATE)

    @app_commands.command(name="bounty", description="cmd.bounty.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_bounty(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, BOUNTY)

    @app_commands.command(name="seasoninfo", description="cmd.seasoninfo.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_seasoninfo(
        self, interact: discord.Interaction, developer_options: bool = True
    ):
        await cmd_helper_maintenance(interact, SEASONINFO)

    @app_commands.command(name="check-queue", description="cmd.check-queue.desc")
    @app_commands.checks.cooldown(
        1, COOLDOWN_DEFAULT, key=lambda i: (i.guild_id, i.user.id)
    )
    async def cmd_check_queue_list(self, interact: discord.Interaction):
        await cmd_helper_maintenance(interact, "check-queue")


async def setup(bot: commands.Bot):
    await bot.add_cog(MaintenanceCommands(bot))
