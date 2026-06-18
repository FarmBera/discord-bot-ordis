import os

import requests

from config.TOKEN import base_url_bounty, BOUNTY_JSON_PATH
from src.constants.color import C
from src.constants.keys import (
    keys,
    JSON,
    DUVIRI_ROTATION,
    ARCHIMEDEA,
    ARCHIMEDEA_DEEP,
    ARCHIMEDEA_TEMPORAL,
)
from src.utils.api_legacy import API_Request
from src.utils.data_manager import get_obj, set_obj
from src.utils.file_io import json_save

print("API Requesting...")
RESPONSE: requests.Response = API_Request()
if RESPONSE.status_code != 200 or not RESPONSE:
    raise ValueError("Response code is NOT 200! Aborted!")
print(f"Done! Code: {RESPONSE.status_code} (eta: {RESPONSE.elapsed})")

dir_base = os.getcwd()


def make_dir():
    pf: str = "mkdir > "
    pf_err: str = "Already exists dir > "

    try:
        os.mkdir(f"{dir_base}/{JSON}")
        print(f"{pf}{JSON}")
    except:
        msg = f"{pf_err}'json'"
        print(C.yellow, msg)

    try:
        os.mkdir("log")
        print(f"{pf}log")
    except:
        msg = f"{pf_err}'log'"
        print(C.yellow, msg)


def make_base_data():
    dir_json = [item.replace(".json", "") for item in os.listdir(f"{dir_base}/{JSON}")]

    obj_origin = RESPONSE.json()
    for item in keys:
        if item in dir_json:
            print(f"{C.green}File exists > {item}.json")  # VAR

        set_obj(obj_origin[item], item)
        print(f"{C.cyan}{item}")

    unique_obj = get_obj(DUVIRI_ROTATION)
    set_obj(unique_obj[0]["CategoryChoices"][0], f"{DUVIRI_ROTATION}Warframe")
    set_obj(unique_obj[0]["CategoryChoices"][1], f"{DUVIRI_ROTATION}Incarnon")
    unique_obj = get_obj(ARCHIMEDEA)
    set_obj(unique_obj[0], f"{ARCHIMEDEA}{ARCHIMEDEA_DEEP}")
    set_obj(unique_obj[1], f"{ARCHIMEDEA}{ARCHIMEDEA_TEMPORAL}")
    print(C.default, end="")


def make_bounty():
    # bounty api
    print("API Requesting Bounty...")
    RESPONSE: requests.Response = API_Request(base_url_bounty, BOUNTY_JSON_PATH)
    if RESPONSE.status_code != 200 or not RESPONSE:
        raise ValueError("Response code is NOT 200! Aborted!")
    print(f"Done! Code: {RESPONSE.status_code} (eta: {RESPONSE.elapsed})")
    json_save(RESPONSE.json(), BOUNTY_JSON_PATH)
    print(C.default, end="")


make_dir()
make_base_data()
make_bounty()
