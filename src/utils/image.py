from config.TOKEN import base_url_warframestat_img
from src.utils.file_io import json_load

NAME_DICTIONARY: dict = json_load("data/en/languages.json")
IMAGE_ORIGIN: dict = json_load("data/item-image-list.json")
IMAGE_CACHE: dict = {}


def getItemName(data: str, query1: str = "value") -> str:
    result = NAME_DICTIONARY.get(data, {}).get(query1)
    return result if result else NAME_DICTIONARY.get(data.lower(), {}).get(query1, data)


def getThumbImg(origin_name: str) -> str:
    global IMAGE_CACHE

    if not origin_name:
        return ""

    parsed_name = getItemName(origin_name).lower().replace(" ", "-")

    # find cached
    cached_name = IMAGE_CACHE.get(parsed_name, None)
    if cached_name:
        return cached_name

    # find items in directory
    for item in IMAGE_ORIGIN:
        finding_name = item.replace(f"-{item.split('-')[-1]}", "")

        if parsed_name == finding_name:
            final_name = f"{base_url_warframestat_img}{item}"
            IMAGE_CACHE[parsed_name] = final_name
            # print(IMAGE_CACHE)  # DEBUG
            return final_name

    return ""  # not found
