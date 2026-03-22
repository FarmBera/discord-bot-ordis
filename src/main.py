import asyncio
import logging
import sys

import aiomysql
import discord

from config.TOKEN import (
    TOKEN as BOT_TOKEN,
    DB_USER,
    DB_PW,
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DEBUG_MODE,
)
from config.config import LOG_TYPE
from src.client.bot_main import DiscordBot
from src.client.bot_maintenance import MaintanceBot
from src.constants.color import C
from src.translator import ts
from src.utils.logging_utils import save_log
from src.utils.return_err import return_traceback, print_test_err

discord.utils.setup_logging(level=logging.INFO, root=False)

db_pool = None

# main thread

ERR_COUNT: int = 0

CMD_MAIN: str = "main"
CMD_MAINTENANCE: str = "maintenance"
CMD_EXIT: str = "exit"

EXIT_CMD: list = [CMD_EXIT, "ㄷ턋", "멱ㅓ"]


async def console_input_listener() -> str | None:
    """
    wait for console input and returns the specified keyword when it is entered.
    """
    while True:
        cmd = await asyncio.to_thread(sys.stdin.readline)
        cmd = cmd.strip().lower()

        if cmd in [CMD_MAIN, CMD_MAINTENANCE] + EXIT_CMD:
            print(f"[info] Console input detected! '{cmd}'")  # VAR
            return cmd
        else:
            print(f"\033[A\rUnknown Command > '{cmd}'")


async def main_manager() -> None:
    """
    manage bot state, and switch bot status depends on console input
    """
    global db_pool

    bot_mode = CMD_MAIN  # init mode
    # bot_mode = input("Starting Bot Mode > ").lower()
    if not bot_mode:
        print(
            f"\033[A\r{C.yellow}Unknown Mode > '{C.red}{bot_mode}{C.yellow}' / setup default mode: {C.cyan}`main`{C.default}"
        )
        bot_mode = CMD_MAIN

    try:  # init db connection
        db_pool = await aiomysql.create_pool(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PW,
            db=DB_NAME,
            autocommit=False,
            minsize=1,
            maxsize=20,
            connect_timeout=5,
        )
        print(f"{C.green}Connected to MariaDB Platform via aiomysql{C.default}")
    except Exception:
        print(
            f"{C.red}Error connecting to MariaDB Platform\n{C.red}\n{return_traceback()}"
        )
        sys.exit(1)

    while bot_mode not in EXIT_CMD:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.members = True
        if bot_mode == CMD_MAIN:
            print(f"{C.cyan}[info] Starting Main Bot...{C.default}")  # VAR
            current_bot = DiscordBot(intents=intents, db=db_pool)

            @current_bot.tree.error
            async def on_app_command_error(
                interact: discord.Interaction,
                error: discord.app_commands.AppCommandError,
            ):
                if isinstance(error, discord.app_commands.CommandOnCooldown):
                    pf = "cmd.err-cooldown."
                    embed = discord.Embed(
                        title=ts.get(f"{pf}title"),
                        description=ts.get(f"{pf}desc").format(
                            time=f"{error.retry_after:.0f}"
                        ),
                        color=0xFF0000,
                    )
                    await interact.response.send_message(embed=embed, ephemeral=True)
                else:  # other type of error
                    msg = f"Unhandled app command error: {error}"
                    await save_log(
                        pool=db_pool, type=LOG_TYPE.err, msg=msg, obj=return_traceback()
                    )
                    print_test_err() if DEBUG_MODE else print(msg)

        elif bot_mode == CMD_MAINTENANCE:
            print(f"{C.magenta}Starting Maintenance Bot...{C.default}", end=" ")  # VAR
            current_bot = MaintanceBot(intents=intents, db=db_pool)

        else:
            break

        print("Creating Task...")
        # create execution task: bot run / console input handler
        bot_task = asyncio.create_task(current_bot.start(BOT_TOKEN))
        console_task = asyncio.create_task(console_input_listener())

        # wait until at least one of the two tasks is completed.
        done, pending = await asyncio.wait(
            [bot_task, console_task], return_when=asyncio.FIRST_COMPLETED
        )

        # verify the completed task is a console input task
        if console_task in done:
            # get input command
            new_mode = console_task.result()
            if new_mode not in EXIT_CMD:
                print(f"Switching Bot... '{bot_mode}' into '{new_mode}'")  # VAR
            bot_mode = new_mode
        else:
            print(
                f"{C.red}[err] The Bot has unexpectedly terminated!{C.default}"
            )  # VAR
            if DEBUG_MODE:
                print_test_err()

            for i in range(5, 0, -1):
                print(
                    f"{C.red}[err] Unexpect Error. Retry in {i}s ",
                    end="\r",
                    flush=True,
                )  # VAR
                await asyncio.sleep(1.0)
            print(f"{C.yellow}Retrying #{ERR_COUNT}{C.default}")
            # bot_mode = "exit"  # exit loop

        # quit currently running bot & skip to next loop
        print(f"{C.default}[info] Terminating current bot...")  # VAR
        await current_bot.close()

        for task in pending:  # cancel remaining task
            task.cancel()

        if bot_mode not in EXIT_CMD:
            for i in range(4, 0, -1):
                print(
                    f"{C.yellow}[info] Executes in {i}s  ",
                    end="\r",
                    flush=True,
                )  # VAR
                await asyncio.sleep(0.98)

    print("[info] Exiting Program...")  # VAR
    # terminate db connection
    print(f"{C.yellow}Terminating DB connection...", end="")
    if db_pool is not None:
        db_pool.close()
        await db_pool.wait_closed()
        print(f"{C.green}Connection Pool closed cleanly.{C.default}")
        db_pool = None


if __name__ == "__main__":
    try:
        asyncio.run(main_manager())
    except KeyboardInterrupt:
        print(f"\n{C.yellow}Force Quitted!")  # VAR
    except Exception as e:
        print(C.red, return_traceback(), sep="")
        ERR_COUNT += 1
        print(f"Continuously Error #{ERR_COUNT} >> {e}")
        # if ERR_COUNT > 20:
        #     sys.exit(1)
