from config.config import language as lang

# commands cooldown time (sec)
CDN: float = 1.0
COOLDOWN_DEFAULT: float = CDN
COOLDOWN_SHORT: float = CDN
COOLDOWN_ACTION: float = CDN
COOLDOWN_CREATE: float = CDN
COOLDOWN_BTN_ACTION: float = CDN  # btn join/leave
COOLDOWN_BTN_MANAGE: float = CDN  # btn modify/remove
COOLDOWN_5_MIN: float = CDN  # 5 minute cooldown
COOLDOWN_BTN_CALL: float = CDN  # btn call members


FIELD_PATTERN: str = "\n"


filePfx: str = f"docs/{lang}/"
fileExt: str = ".md"
configPfx: str = "config/"
JSON: str = "api_cache"

# json file location
# DEFAULT_JSON_PATH: str = f"data/Warframe.json"
# DEFAULT_MARKET_JSON_PATH: str = f"data/market-search.json"

# other file location
SETTING_FILE_LOC: str = f"{configPfx}setting.json"
# docs file list
HELP_FILE_LOC: str = f"{filePfx}help{fileExt}"
ANNOUNCE_FILE_LOC: str = f"{filePfx}announcement{fileExt}"
PATCHNOTE_FILE_LOC: str = f"{filePfx}patch-note{fileExt}"
POLICY_FILE_LOC: str = f"{filePfx}privacy-policy{fileExt}"
FOOTER_FILE_LOC: str = f"{filePfx}footer{fileExt}"


MSG_BOT: str = "bot.self"

# cached worldstate data
ALERTS: str = "Alerts"
NEWS: str = "Events"
CETUSCYCLE: str = "cetusCycle"
SORTIE: str = "Sorties"
ARCHONHUNT: str = "LiteSorties"
VOIDTRADERS: str = "VoidTraders"
STEELPATH: str = "steelPath"
DUVIRICYCLE: str = "duviriCycle"
ARCHIMEDEA: str = "Conquests"
FISSURES: str = "ActiveMissions"
CALENDAR: str = "KnownCalendarSeasons"
CAMBIONCYCLE: str = "cambionCycle"
DAILYDEALS: str = "DailyDeals"
INVASIONS: str = "Invasions"
MARKET_SEARCH: str = "market-search"
VALLISCYCLE: str = "vallisCycle"
DUVIRI_ROTATION: str = "EndlessXpSchedule"
EVENTS: str = "Goals"
EVENT_BOOSTER: str = ""
DESCENDIA: str = "Descents"
ARBITRATION: str = "arbitration"
WORLDSTATE: str = "WorldState"
BOUNTY: str = "Bounty"
SEASONINFO: str = "SeasonInfo"

DUVIRI_U_K_W: str = "Warframe"
DUVIRI_U_K_I: str = "Incarnon"
DUVIRI_CACHE: str = "data/RotationDuviri.json"

ARCHIMEDEA_DEEP: str = "Deep"
ARCHIMEDEA_TEMPORAL: str = "Temporal"

# keys to refresh api_cache JSON
keys: list = [
    ALERTS,
    NEWS,
    SORTIE,
    ARCHONHUNT,
    VOIDTRADERS,
    ARCHIMEDEA,
    FISSURES,
    CALENDAR,
    DAILYDEALS,
    INVASIONS,
    DUVIRI_ROTATION,
    EVENTS,
    DESCENDIA,
    SEASONINFO,
]

LFG_WEBHOOK_NAME: str = "meow-bot-profile"

# special items for invasions
SPECIAL_ITEM_LIST: list = [
    # en
    "exilus",
    "orokin",
    "reactor",
    "forma",
    # ko
    "오로킨",
    "포르마",
    "엑실러스",
]
