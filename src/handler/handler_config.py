from src.constants.keys import (
    ALERTS,
    NEWS,
    SORTIE,
    ARCHONHUNT,
    VOIDTRADERS,
    # STEELPATH,
    DUVIRICYCLE,
    FISSURES,
    ARCHIMEDEA,
    ARCHIMEDEA_DEEP,
    ARCHIMEDEA_TEMPORAL,
    CALENDAR,
    DAILYDEALS,
    INVASIONS,
    DUVIRI_ROTATION,
    DUVIRI_U_K_W,
    DUVIRI_U_K_I,
    EVENTS,
    CETUSCYCLE,
    CAMBIONCYCLE,
    VALLISCYCLE,
    BOUNTY,
    DESCENDIA,
    SEASONINFO,
)
from src.parser.alerts import w_alerts
from src.parser.archimedea import w_deepArchimedea, w_temporalArchimedia
from src.parser.archonHunt import w_archonHunt
from src.parser.bounty import w_bounty
from src.parser.calendar import w_calendar
from src.parser.cambionCycle import w_cambionCycle, checkNewCambionState
from src.parser.cetusCycle import w_cetusCycle, checkNewCetusState
from src.parser.dailyDeals import w_dailyDeals, getDarvoRandomMsg
from src.parser.descendia import w_descendia
from src.parser.duviriCycle import w_duviriCycle, checkNewDuviriState
from src.parser.duviriRotation import w_duviri_warframe, w_duviri_incarnon
from src.parser.events import w_events
from src.parser.invasions import w_invasions_se
from src.parser.news import w_news
from src.parser.seasoninfo import w_nightwave
from src.parser.sortie import w_sortie
from src.parser.vallisCycle import w_vallisCycle, checkNewVallisState
from src.parser.voidTraders import w_voidTraders, getBaroRandomMsg


class HK:
    key = "key"
    parser = "parser"
    special_logic = "special_logic"
    update_check = "update_check"
    arg_func = "arg_func"


class LOGIC:
    no_args = "handle_no_args"
    missing = "handle_missing_items"
    news = "handle_new_news"
    bounty = "handle_bounty"
    invasions = "handle_missing_invasions"
    fissures = "handle_fissures"
    voidtraders = "handle_voidtraders"
    deep_archimedea = "handle_deep_archimedea"
    temporal_archimedea = "handle_temporal_archimedea"
    duviri_wf = "handle_duviri_rotation-1"
    duviri_inc = "handle_duviri_rotation-2"
    seasoninfo = "handle_seasoninfo"


DATA_HANDLERS = {
    ALERTS: {
        HK.parser: w_alerts,
        HK.special_logic: LOGIC.missing,
    },
    NEWS: {
        HK.parser: w_news,
        HK.special_logic: LOGIC.news,
    },
    CETUSCYCLE: {
        HK.parser: w_cetusCycle,
        HK.special_logic: LOGIC.no_args,
        HK.update_check: checkNewCetusState,
    },
    SORTIE: {
        HK.parser: w_sortie,
        HK.update_check: lambda prev, new: prev[0]["_id"]["$oid"]
        != new[0]["_id"]["$oid"]
        or prev[0]["Activation"]["$date"] != new[0]["Activation"]["$date"],
    },
    ARCHONHUNT: {
        HK.parser: w_archonHunt,
        HK.update_check: lambda prev, new: prev[0]["Activation"]
        != new[0]["Activation"],
    },
    VOIDTRADERS: {
        HK.parser: w_voidTraders,
        HK.special_logic: LOGIC.voidtraders,
        HK.arg_func: getBaroRandomMsg,
    },
    DUVIRICYCLE: {
        HK.parser: w_duviriCycle,
        HK.special_logic: LOGIC.no_args,
        HK.update_check: checkNewDuviriState,
    },
    FISSURES: {HK.special_logic: LOGIC.fissures},
    f"{ARCHIMEDEA}{ARCHIMEDEA_DEEP}": {
        HK.key: ARCHIMEDEA,
        HK.parser: w_deepArchimedea,
        HK.special_logic: LOGIC.deep_archimedea,
    },
    f"{ARCHIMEDEA}{ARCHIMEDEA_TEMPORAL}": {
        HK.key: ARCHIMEDEA,
        HK.parser: w_temporalArchimedia,
        HK.special_logic: LOGIC.temporal_archimedea,
    },
    CALENDAR: {
        HK.parser: lambda data, **kwargs: w_calendar(data, **kwargs),
        HK.update_check: lambda prev, new: prev[0]["Activation"]["$date"]["$numberLong"]
        != new[0]["Activation"]["$date"]["$numberLong"],
    },
    CAMBIONCYCLE: {
        HK.parser: w_cambionCycle,
        HK.special_logic: LOGIC.no_args,
        HK.update_check: checkNewCambionState,
    },
    DAILYDEALS: {
        HK.parser: w_dailyDeals,
        HK.update_check: lambda prev, new: prev[0]["StoreItem"] != new[0]["StoreItem"],
        HK.arg_func: getDarvoRandomMsg,
    },
    INVASIONS: {
        HK.parser: w_invasions_se,
        HK.special_logic: LOGIC.invasions,
    },
    f"{DUVIRI_ROTATION}{DUVIRI_U_K_W}": {  # circuit-warframe
        HK.key: DUVIRI_ROTATION,
        HK.parser: w_duviri_warframe,
        HK.special_logic: LOGIC.duviri_wf,
    },
    f"{DUVIRI_ROTATION}{DUVIRI_U_K_I}": {  # circuit-incarnon
        HK.key: DUVIRI_ROTATION,
        HK.parser: w_duviri_incarnon,
        HK.special_logic: LOGIC.duviri_inc,
    },
    EVENTS: {
        HK.parser: w_events,
        HK.special_logic: LOGIC.missing,
    },
    VALLISCYCLE: {
        HK.parser: w_vallisCycle,
        HK.special_logic: LOGIC.no_args,
        HK.update_check: checkNewVallisState,
    },
    BOUNTY: {
        HK.parser: w_bounty,
        HK.special_logic: LOGIC.bounty,
    },
    DESCENDIA: {
        HK.parser: w_descendia,
        HK.update_check: lambda prev, new: prev[0]["Activation"]["$date"]["$numberLong"]
        != new[0]["Activation"]["$date"]["$numberLong"],
    },
    SEASONINFO: {
        HK.parser: w_nightwave,
        HK.special_logic: LOGIC.seasoninfo,
    },
}
