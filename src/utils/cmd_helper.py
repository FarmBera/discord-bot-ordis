import discord

from config.config import LOG_TYPE
from src.constants.color import C
from src.constants.keys import FOOTER_FILE_LOC
from src.translator import ts, get_ts, locale_to_lang
from src.utils.data_manager import get_obj_async
from src.utils.discord_file import img_file
from src.utils.file_io import open_file_async
from src.utils.logging_utils import save_log
from src.utils.permission import is_admin_user, is_banned_user
from src.utils.return_err import err_embed, return_traceback
from src.views.consent_view import check_consent
from src.views.help_view import SupportMasterView, SupportView


async def cmd_helper(
    interact: discord.Interaction,
    key: str,
    parser_func,
    isFollowUp: bool = False,
    parser_args=None,
    isPrivateMsg: bool = True,
    isMarketQuery: bool = False,
    marketQuery: tuple = (None, None),
    skipGetObj: bool = False,
) -> None:
    if await is_banned_user(interact):
        return
    if not await check_consent(interact):
        return

    # check admin if user want to send public msg
    if not isPrivateMsg:
        is_admin = await is_admin_user(
            interact=interact, cmd=f"{parser_func}//{parser_args}//MARKET:{marketQuery}"
        )
        if not is_admin:
            isPrivateMsg = True

    if isFollowUp:
        await interact.response.defer(ephemeral=isPrivateMsg)

    # parse objects
    user_ts = get_ts(interact.locale)
    user_lang = locale_to_lang(interact.locale)
    if skipGetObj:
        obj = parser_func(ts=user_ts, lang=user_lang)
    elif parser_args:
        obj = parser_func(
            await get_obj_async(key), parser_args, ts=user_ts, lang=user_lang
        )
    elif isMarketQuery:
        obj = await parser_func(
            interact.client.db, marketQuery, ts=user_ts, lang=user_lang
        )
    else:
        obj = parser_func(await get_obj_async(key), ts=user_ts, lang=user_lang)

    # send message
    resp_head = interact.followup if isFollowUp else interact.response

    # check object type
    if isinstance(obj, discord.Embed):  # embed only
        if isFollowUp:
            await resp_head.send(embed=obj, ephemeral=isPrivateMsg)
        else:
            await resp_head.send_message(embed=obj, ephemeral=isPrivateMsg)
        log_obj = obj.description
    elif isinstance(obj, tuple):  # embed with file (Modified)
        view, file = None, None

        if isMarketQuery:
            eb, view = obj
        else:
            eb, file = obj

        # default args
        send_kwargs = {"embed": eb, "ephemeral": isPrivateMsg}
        if isMarketQuery and view:
            send_kwargs["view"] = view
        if file:
            send_kwargs["file"] = img_file(file)

        if isFollowUp:
            await resp_head.send(**send_kwargs)
        else:
            await resp_head.send_message(**send_kwargs)

        log_obj = eb.description
    else:  # text only
        if isFollowUp:
            await resp_head.send(obj, ephemeral=isPrivateMsg)
        else:
            await resp_head.send_message(obj, ephemeral=isPrivateMsg)
        log_obj = obj

    await save_log(
        pool=interact.client.db,
        type=LOG_TYPE.cmd,
        cmd=f"{LOG_TYPE.cmd}.{key}{f'-{parser_args}' if parser_args else ''}",
        interact=interact,
        msg="cmd responsed",  # VAR
        obj=log_obj,
    )


async def cmd_helper_txt(
    interact: discord.Interaction, file_name: str, isPrivateMsg: bool = True
) -> None:
    if await is_banned_user(interact):
        return
    if await check_consent(interact):
        return

    if not isPrivateMsg:
        is_admin = await is_admin_user(interact=interact, cmd=f"{file_name}")
        if not is_admin:
            isPrivateMsg = True

    # open & read file
    try:
        txt1 = await open_file_async(file_name)
        txt2 = await open_file_async(FOOTER_FILE_LOC)
        txt = txt1 + txt2
    except Exception as e:  # send err msg
        msg: str = "open_file err in cmd_helper_txt"  # VAR
        await interact.response.send_message(
            embed=err_embed(file_name), view=SupportView(), ephemeral=True
        )
        print(C.red, msg, C.default, sep="")
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.err,
            cmd="cmd_helper_txt",
            interact=interact,
            msg=f"{msg}: {e}",
            obj=return_traceback(),
        )
        return

    # send message
    await interact.response.send_message(
        embed=discord.Embed(description=txt, color=0xCEFF00),  # VAR: color
        view=SupportMasterView(),
        ephemeral=isPrivateMsg,
    )

    await save_log(
        pool=interact.client.db,
        type=LOG_TYPE.cmd,
        cmd=f"{LOG_TYPE.cmd}.{ts.get(f'cmd.help.cmd')}",
        interact=interact,
        msg="cmd used",  # VAR
        obj=f"{isPrivateMsg}\n{txt}",
    )
