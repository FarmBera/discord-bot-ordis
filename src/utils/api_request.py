import httpx
import orjson

from config.TOKEN import base_url_warframe, base_url_market, WF_JSON_PATH
from config.config import LOG_TYPE
from src.constants.color import C
from src.constants.keys import MSG_BOT
from src.translator import language as lang
from src.utils.file_io import json_save_async
from src.utils.logging_utils import save_log
from src.utils.return_err import return_traceback
from src.utils.times import timeNowDT

HttpxClient = httpx.AsyncClient(timeout=60)
params_market: dict = {"Language": lang, "Platform": "pc"}


async def API_internal(pool, url=base_url_warframe):
    start_time = timeNowDT()

    # API Request
    try:
        response = await HttpxClient.get(url)
    except httpx.HTTPError as e:
        elapsed_time = timeNowDT() - start_time
        msg = f"API request failed!: {elapsed_time}/{e}"
        print(timeNowDT(), C.red, msg, C.default)
        await save_log(
            pool=pool,
            type=LOG_TYPE.err,
            cmd="API_Request()",
            user=MSG_BOT,
            msg=msg,
            obj=return_traceback(),
        )
        return None

    # check response code
    res_code: int = response.status_code
    if res_code != 200:
        elapsed_time = timeNowDT() - start_time
        msg = f"response code is not 200: {res_code}/{elapsed_time}"
        await save_log(
            pool=pool,
            type=LOG_TYPE.err,
            cmd="API_Request()",
            user=MSG_BOT,
            msg=msg,
        )
        print(timeNowDT(), C.red, msg, C.default)
        return response

    # check response body is not empty
    if not response.content:
        elapsed_time = timeNowDT() - start_time
        msg = f"response is Empty!: {res_code}/{elapsed_time}"
        print(timeNowDT(), C.red, msg, C.default)
        await save_log(
            pool=pool,
            type=LOG_TYPE.err,
            cmd="API_Request()",
            user=MSG_BOT,
            msg=msg,
            obj=response.text,
        )
        return None

    # validate that the body is parseable JSON before returning
    try:
        orjson.loads(response.content)
    except orjson.JSONDecodeError:
        msg = f"invalid JSON response: {response.status_code}"
        print(C.red, msg, C.default)
        await save_log(
            pool=pool,
            type=LOG_TYPE.err,
            cmd="API_Request()",
            user=MSG_BOT,
            msg=msg,
            obj=response.text,
        )
        return None

    return response


# usage for main api
async def API_Request(pool, URL=base_url_warframe, fname=WF_JSON_PATH):
    """API request function for Warframe status

    :param pool: aiomysql cursor pool
    :param URL: request url
    :param fname:
    :return:
        None: failed to request api
        dict: successfully parsed object
    """
    response = await API_internal(pool, URL)
    if not response:
        return None

    await json_save_async(response.json(), fname)
    return response


# usage for market api
async def API_MarketSearch(pool, item_name: str):
    try:
        response = await HttpxClient.get(
            f"{base_url_market}orders/item/{item_name}",
            headers=params_market,
        )
    except httpx.HTTPError as e:
        msg = f"API request failed!: {e}"
        print(timeNowDT(), C.red, msg, C.default)
        await save_log(
            pool=pool,
            type=LOG_TYPE.err,
            cmd="API_MarketSearch()",
            user=MSG_BOT,
            msg=msg,
            obj=return_traceback(),
        )
        return None

    msg = f"{response.status_code}//{item_name}//{response.elapsed}"
    await save_log(
        pool=pool,
        type=LOG_TYPE.api,
        cmd="API_MarketSearch()",
        user=MSG_BOT,
        msg=msg,
    )

    return response
