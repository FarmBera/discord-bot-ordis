from src.constants.keys import (
    ALERTS,
    NEWS,
    SORTIE,
    ARCHONHUNT,
    VOIDTRADERS,
    STEELPATH,
    ARCHIMEDEA,
    CALENDAR,
    DAILYDEALS,
    INVASIONS,
    DUVIRI_ROTATION,
    EVENTS,
    #
    DUVIRI_U_K_W,
    DUVIRI_U_K_I,
    #
    ARCHIMEDEA_DEEP,
    ARCHIMEDEA_TEMPORAL,
    CETUSCYCLE,
    DUVIRICYCLE,
    CAMBIONCYCLE,
    VALLISCYCLE,
    BOUNTY,
    DESCENDIA,
)
from src.translator import ts

DB_COLUMN_MAP = {
    ALERTS: "sub_alerts",
    NEWS: "sub_news",
    SORTIE: "sub_sortie",
    ARCHONHUNT: "sub_archonhunt",
    VOIDTRADERS: "sub_voidtraders",
    f"{ARCHIMEDEA}{ARCHIMEDEA_DEEP}": "sub_darchimedea",
    f"{ARCHIMEDEA}{ARCHIMEDEA_TEMPORAL}": "sub_tarchimedea",
    STEELPATH: "sub_steelpath",
    CALENDAR: "sub_calendar",
    DAILYDEALS: "sub_dailydeals",
    INVASIONS: "sub_invasions",
    f"{DUVIRI_ROTATION}{DUVIRI_U_K_W}": "sub_duviri_wf",
    f"{DUVIRI_ROTATION}{DUVIRI_U_K_I}": "sub_duviri_inc",
    EVENTS: "sub_events",
    CETUSCYCLE: "sub_cetus",
    DUVIRICYCLE: "sub_duviri",
    CAMBIONCYCLE: "sub_cambion",
    VALLISCYCLE: "sub_vallis",
    BOUNTY: "sub_bounty",
    DESCENDIA: "sub_descend",
}

# UI selection
PF_LABEL: str = "noti-label."
NOTI_LABELS = {
    ALERTS: ts.get(f"{PF_LABEL}{ALERTS}"),
    NEWS: ts.get(f"{PF_LABEL}{NEWS}"),
    SORTIE: ts.get(f"{PF_LABEL}{SORTIE}"),
    ARCHONHUNT: ts.get(f"{PF_LABEL}{ARCHONHUNT}"),
    VOIDTRADERS: ts.get(f"{PF_LABEL}{VOIDTRADERS}"),
    f"{ARCHIMEDEA}{ARCHIMEDEA_DEEP}": ts.get(
        f"{PF_LABEL}{ARCHIMEDEA}{ARCHIMEDEA_DEEP}"
    ),
    f"{ARCHIMEDEA}{ARCHIMEDEA_TEMPORAL}": ts.get(
        f"{PF_LABEL}{ARCHIMEDEA}{ARCHIMEDEA_TEMPORAL}"
    ),
    STEELPATH: ts.get(f"{PF_LABEL}{STEELPATH}"),
    CALENDAR: ts.get(f"{PF_LABEL}{CALENDAR}"),
    DAILYDEALS: ts.get(f"{PF_LABEL}{DAILYDEALS}"),
    INVASIONS: ts.get(f"{PF_LABEL}{INVASIONS}"),
    f"{DUVIRI_ROTATION}{DUVIRI_U_K_W}": ts.get(
        f"{PF_LABEL}{DUVIRI_ROTATION}{DUVIRI_U_K_W}"
    ),
    f"{DUVIRI_ROTATION}{DUVIRI_U_K_I}": ts.get(
        f"{PF_LABEL}{DUVIRI_ROTATION}{DUVIRI_U_K_I}"
    ),
    EVENTS: ts.get(f"{PF_LABEL}{EVENTS}"),
    CETUSCYCLE: ts.get(f"{PF_LABEL}{CETUSCYCLE}"),
    DUVIRICYCLE: ts.get(f"{PF_LABEL}{DUVIRICYCLE}"),
    CAMBIONCYCLE: ts.get(f"{PF_LABEL}{CAMBIONCYCLE}"),
    VALLISCYCLE: ts.get(f"{PF_LABEL}{VALLISCYCLE}"),
    BOUNTY: ts.get(f"{PF_LABEL}{BOUNTY}"),
    DESCENDIA: ts.get(f"{PF_LABEL}{DESCENDIA}"),
}

# profile name & image
PROFILE_CONFIG: dict = {
    VOIDTRADERS: {"name": ts.get(f"{PF_LABEL}trader"), "avatar": "baro"},
    f"{ARCHIMEDEA}{ARCHIMEDEA_DEEP}": {
        "name": ts.get(f"{PF_LABEL}deep"),
        "avatar": "deep",
    },
    f"{ARCHIMEDEA}{ARCHIMEDEA_TEMPORAL}": {
        "name": ts.get(f"{PF_LABEL}temporal"),
        "avatar": "temporal",
    },
    DAILYDEALS: {"name": ts.get(f"{PF_LABEL}darvo"), "avatar": "darvo"},
}

pfs: str = "cmd.alert-set."  # prefix select
pfu: str = "cmd.alert-delete."  # prefix unselect
