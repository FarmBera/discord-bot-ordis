import datetime as dt

import discord
from discord import ui
from discord.ext import commands

from config.config import LOG_TYPE
from src.constants.keys import (
    COOLDOWN_BTN_CALL,
    COOLDOWN_ACTION,
    COOLDOWN_SHORT,
)
from src.services.party_service import PartyService
from src.services.queue_manager import add_job, JobType
from src.translator import ts
from src.utils.logging_utils import save_log
from src.utils.permission import (
    is_cooldown,
    is_admin_user,
    is_banned_user,
)
from src.utils.return_err import return_traceback
from src.utils.times import convert_remain, parseKoreanDatetime
from src.views.consent_view import check_consent
from src.views.help_view import SupportView

pf = "cmd.party."
MIN_SIZE = 2
MAX_SIZE = 20


async def isPartyExist(interact: discord.Interaction, party):
    if party:
        return True

    embed = discord.Embed(
        title=ts.get(f"{pf}err"),
        description=ts.get(f"{pf}pv-not-found"),
        color=discord.Color.red(),
    )
    await interact.response.send_message(embed=embed, ephemeral=True)
    await save_log(
        pool=interact.client.db,
        type=LOG_TYPE.err,
        cmd="btn",
        msg="party not found from db",
        interact=interact,
    )
    return False


# ----------------- Helper: Embed Builder -----------------
async def build_party_embed(
    data: dict, db_pool, isDelete: bool = False
) -> discord.Embed:
    color = discord.Color.orange() if data.get("is_closed") else discord.Color.blue()
    description: str = ""

    # host warning check
    # description += await WarnService.generateWarnMsg(db_pool, data["host_id"])

    status_text = (
        f"({ts.get(f'{pf}pv-done')})"
        if data.get("is_closed")
        else f"({ts.get(f'{pf}pv-ing2')})"
    )
    participants_str = ", ".join(data["participants"]) or ts.get(f"{pf}pb-no-player")
    desc_field = data.get("description", "")

    departure_data = data["departure"]
    if isinstance(departure_data, dt.datetime):
        time_output = convert_remain(departure_data.timestamp())
    else:
        time_output = (
            convert_remain(parseKoreanDatetime(departure_data).timestamp())
            if departure_data
            else ts.get(f"{pf}pb-departure-none")
        )

    description += f"""### {data['title']} {status_text}
- **{ts.get(f'{pf}pb-departure')}:** {time_output}
- **{ts.get(f'{pf}pb-host')}:** {data['host_mention']}
- **{ts.get(f'{pf}pb-player-count')}:** {len(data['participants'])} / {data['max_users']}
- **{ts.get(f'{pf}pb-player-joined')}:** {participants_str}
- **{ts.get(f'{pf}pb-mission')}:** {data['mission']}

{desc_field}"""

    if isDelete:
        description = "~~" + description.replace("~~", "") + "~~"

    embed = discord.Embed(
        description=description.strip(), color=color if not isDelete else 0xFF0000
    )
    embed.set_footer(text=f"{ts.get(f'{pf}pb-pid')}: {data['id']}")
    return embed


async def build_party_embed_from_db(message_id: int, pool, isDelete: bool = False):
    party, participants = await PartyService.get_party_by_message_id(pool, message_id)
    if not party:
        return discord.Embed(
            title=ts.get(f"{pf}err"),
            description=ts.get(f"{pf}pv-not-found"),
            color=discord.Color.dark_red(),
        )

    host_mention = f"<@{party['host_id']}>"
    # find specific host mention if available in participants
    for p in participants:
        if p["user_id"] == party["host_id"]:
            host_mention = p["user_mention"]
            break

    return await build_party_embed(
        {
            "id": party["id"],
            "host_id": party["host_id"],
            "is_closed": party["status"] == ts.get(f"{pf}pv-done"),
            "title": party["title"],
            "host_mention": host_mention,
            "max_users": party["max_users"],
            "participants": [p["user_mention"] for p in participants],
            "mission": party["game_name"],
            "departure": party["departure"],
            "description": party["description"] or "",
        },
        pool,
        isDelete,
    )


# ----------------- Modals -----------------
class PartyEditAllModal(ui.Modal, title=ts.get(f"{pf}edit-all-title")):
    def __init__(self, party_data: dict, participants: list):
        super().__init__(timeout=None)

        self.current_title = party_data["title"] or ""
        self.current_mission = party_data["game_name"] or ""
        self.current_desc = party_data["description"] or ""
        self.current_max_users = int(party_data["max_users"])
        self.participants_count = len(participants)

        self.title_input = ui.TextInput(
            label=ts.get(f"{pf}edit-title-input"),
            default=self.current_title,
            required=True,
        )
        self.add_item(self.title_input)

        self.mission_input = ui.TextInput(
            label=ts.get(f"{pf}edit-mission-input"),
            default=self.current_mission,
            required=True,
        )
        self.add_item(self.mission_input)

        self.size_input = ui.TextInput(
            label=ts.get(f"{pf}size-label"),
            default=str(self.current_max_users),
            required=True,
        )
        self.add_item(self.size_input)

        self.date_input = ui.TextInput(
            label=ts.get(f"{pf}date-input"),
            placeholder=ts.get(f"{pf}date-placeholder"),
            default="",  # blank = keep existing departure
            required=False,
        )
        self.add_item(self.date_input)

        self.desc_input = ui.TextInput(
            label=ts.get(f"{pf}edit-desc-input"),
            style=discord.TextStyle.long,
            default=self.current_desc,
            required=False,
        )
        self.add_item(self.desc_input)

    async def on_submit(self, interact: discord.Interaction):
        # Validate all fields together, collect errors
        errors: list[str] = []

        new_title: str | None = None
        new_mission: str | None = None
        new_description: str | None = None
        new_max_users: int | None = None
        new_departure = None

        # title
        title_val = self.title_input.value.strip()
        if not title_val:
            errors.append(
                f"- {ts.get(f'{pf}edit-title-input')}: "
                f"{ts.get(f'{pf}edit-err-empty')}"
            )
        else:
            new_title = title_val

        # mission
        mission_val = self.mission_input.value.strip()
        if not mission_val:
            errors.append(
                f"- {ts.get(f'{pf}edit-mission-input')}: "
                f"{ts.get(f'{pf}edit-err-empty')}"
            )
        else:
            new_mission = mission_val

        new_description = self.desc_input.value

        # max participants
        size_str = self.size_input.value.strip()
        if not size_str.isdigit():
            errors.append(
                f"- {ts.get(f'{pf}size-label')}: "
                f"{ts.get(f'{pf}size-err-low').format(min=MIN_SIZE, max=MAX_SIZE)}"
            )
        else:
            parsed_size = int(size_str)
            if parsed_size < MIN_SIZE or parsed_size > MAX_SIZE:
                errors.append(
                    f"- {ts.get(f'{pf}size-label')}: "
                    f"{ts.get(f'{pf}size-err-high').format(max=MAX_SIZE)}"
                )
            elif parsed_size < self.participants_count:
                errors.append(
                    f"- {ts.get(f'{pf}size-label')}: "
                    f"{ts.get(f'{pf}size-err-high-1').format(size=self.participants_count)}"
                )
            else:
                new_max_users = parsed_size

        # departure
        date_val = self.date_input.value.strip()
        if date_val:
            try:
                parsed_dt = parseKoreanDatetime(date_val)
            except Exception:
                parsed_dt = None
            if parsed_dt is None:
                errors.append(
                    f"- {ts.get(f'{pf}date-input')}: "
                    f"{ts.get(f'{pf}date-err-parse')}"
                )
            else:
                new_departure = parsed_dt

        if errors:
            await interact.response.send_message("\n".join(errors), ephemeral=True)
            return

        diff_kwargs: dict = {}
        change_log: list[str] = []

        if new_title is not None and new_title != self.current_title:
            diff_kwargs["title"] = new_title
            change_log.append("title")
        if new_mission is not None and new_mission != self.current_mission:
            diff_kwargs["mission"] = new_mission
            change_log.append("mission")
        if new_description != self.current_desc:
            diff_kwargs["description"] = new_description
            change_log.append("desc")
        if new_max_users is not None and new_max_users != self.current_max_users:
            diff_kwargs["max_users"] = new_max_users
            change_log.append(f"size:{self.current_max_users}->{new_max_users}")
        if new_departure is not None:
            # Departure comparison: only send if user actually typed a value;
            diff_kwargs["departure"] = new_departure
            change_log.append(f"departure:{date_val}")

        if not diff_kwargs:
            await interact.response.send_message(
                ts.get(f"{pf}edit-no-change"), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.event,
                cmd="btn.edit.party",
                interact=interact,
                msg="PartyEditAllModal -> Submit, no change",
            )
            return

        try:
            await PartyService.update_party_info(
                interact.client.db, interact.message.id, **diff_kwargs
            )
            await add_job(JobType.PARTY_UPDATE, {"interact": interact, "self": self})
            await interact.client.trigger_queue_processing()
            await interact.response.send_message(
                ts.get(f"{pf}edit-requested"), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.event,
                cmd="btn.edit.party",
                interact=interact,
                msg=f"PartyEditAllModal -> Submit {', '.join(change_log)}",
            )
        except Exception:
            if not interact.response.is_done():
                await interact.response.send_message(
                    ts.get(f"{pf}edit-err"), view=SupportView(), ephemeral=True
                )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd="btn.edit.party",
                interact=interact,
                msg="PartyEditAllModal -> Submit, but ERR",
                obj=(
                    f"T:{title_val}\nM:{mission_val}\nSIZE:{size_str}\n"
                    f"DATE:{date_val}\nDESC:{self.desc_input.value}\n"
                    f"{return_traceback()}"
                ),
            )


# ----------------- Views -----------------
class ConfirmJoinLeaveView(ui.View):
    def __init__(self, action, party_id, interact: discord.Interaction, host_id):
        super().__init__(timeout=20)
        self.action = action
        self.db_pool = interact.client.db
        self.party_id = party_id
        self.user_id = interact.user.id
        self.user_mention = interact.user.mention
        self.original_message = interact.message
        self.interact = interact
        self.host_id = host_id

    async def on_timeout(self):
        cmd = "PartyView.btn.confirm.join/leave"
        try:
            await self.interact.edit_original_response(
                content=ts.get(f"cmd.err-timeout"), view=None
            )
            await save_log(
                pool=self.db_pool,
                type=LOG_TYPE.event,
                cmd=cmd,
                interact=self.interact,
                msg=f"PartyView.ConfirmJoinLeaveView -> timeout",
            )
        except discord.NotFound:
            await save_log(
                pool=self.interact.client.db,
                type=LOG_TYPE.info,
                cmd=cmd,
                interact=self.interact,
                msg=f"PartyView.ConfirmJoinLeaveView -> timeout, but Not Found",
                obj=return_traceback(),
            )
        except Exception:
            await save_log(
                pool=self.db_pool,
                type=LOG_TYPE.err,
                cmd=cmd,
                interact=self.interact,
                msg=f"PartyView.ConfirmJoinLeaveView -> timeout, but ERR",
                obj=return_traceback(),
            )

    @ui.button(label=ts.get(f"{pf}del-btny"), style=discord.ButtonStyle.success)
    async def yes_button(self, interact: discord.Interaction, button: ui.Button):
        try:
            if self.action == "join":
                await save_log(
                    pool=interact.client.db,
                    type=LOG_TYPE.event,
                    cmd="btn.confirm.join",
                    interact=interact,
                    msg=f"ConfirmJoinLeaveView -> action join",
                )
                await PartyService.join_participant(
                    self.db_pool,
                    self.party_id,
                    self.user_id,
                    self.user_mention,
                    interact.user.display_name,
                )
                await interact.response.edit_message(
                    content=ts.get(f"{pf}pv-joined"), view=None
                )
                # TODO: random join message
                rint = 1
                msg_content = ts.get(f"{pf}pc-joined{rint}").format(
                    host=f"<@{self.host_id}>", user=self.user_mention
                )
                # user warn msg
                # msg_content += WarnService.generateWarnMsg(self.db_pool, interact.user.id)
                await self.original_message.channel.send(msg_content)
            elif self.action == "leave":
                await save_log(
                    pool=interact.client.db,
                    type=LOG_TYPE.event,
                    cmd="btn.confirm.leave",
                    interact=interact,
                    msg=f"ConfirmJoinLeaveView -> action leave",
                )
                await PartyService.leave_participant(
                    self.db_pool, self.party_id, self.user_id
                )
                await interact.response.edit_message(
                    content=ts.get(f"{pf}pv-exited"), view=None
                )
                # send a public message to the thread channel
                # user warn msg
                msg_content = ts.get(f"{pf}pc-lefted").format(
                    host=self.user_mention, user=interact.user.mention
                )
                # user warn msg
                # msg_content += WarnService.generateWarnMsg(self.db_pool,interact.user.id)
                await self.original_message.channel.send(msg_content)
            await add_job(JobType.PARTY_UPDATE, {"origin_msg": self.original_message})
            await interact.client.trigger_queue_processing()
        except Exception as e:
            if not interact.response.is_done():
                await interact.response.edit_message(
                    content=ts.get("general.error-cmd") + ts.get(f"{pf}already"),
                    view=SupportView(),
                )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd="btn.confirm.err",
                interact=interact,
                msg=f"ConfirmJoinLeaveView -> action join or levae but ERR:",
                obj=f"{e}\n{return_traceback()}",
            )
        self.stop()

    @ui.button(label=ts.get(f"{pf}del-btnn"), style=discord.ButtonStyle.secondary)
    async def no_button(self, interact: discord.Interaction, button: ui.Button):
        await interact.response.edit_message(
            content=ts.get(f"{pf}del-cancel"), view=None
        )
        self.stop()
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd="btn.confirm.delete.cancel",
            interact=interact,
            msg=f"ConfirmJoinLeaveView -> clicked no",
        )


class ConfirmDeleteView(ui.View):
    def __init__(
        self, interact: discord.Interaction, origin_message: discord.Message, party_view
    ):
        super().__init__(timeout=20)
        self.interact = interact
        self.origin_message = origin_message
        self.party_view = party_view
        self.value = None

    async def on_timeout(self):
        cmd = "PartyView.btn.confirm.delete"
        try:
            await self.interact.edit_original_response(
                content=ts.get(f"cmd.err-timeout"), view=None
            )
            await save_log(
                pool=self.interact.client.db,
                type=LOG_TYPE.event,
                cmd=cmd,
                interact=self.interact,
                msg=f"PartyView.ConfirmDeleteView -> timeout",
            )
        except discord.NotFound:
            await save_log(
                pool=self.interact.client.db,
                type=LOG_TYPE.warn,
                cmd=cmd,
                interact=self.interact,
                msg=f"PartyView.ConfirmDeleteView -> timeout, but Not Found",
            )
        except Exception:
            await save_log(
                pool=self.interact.client.db,
                type=LOG_TYPE.err,
                cmd=cmd,
                interact=self.interact,
                msg=f"PartyView.ConfirmDeleteView -> timeout, but ERR",
                obj=return_traceback(),
            )

    @ui.button(label=ts.get(f"{pf}del-btny"), style=discord.ButtonStyle.danger)
    async def yes_button(self, interact: discord.Interaction, button: ui.Button):
        await interact.response.defer(ephemeral=True)
        await self.origin_message.edit(view=None)
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd="btn.confirm.delete",
            interact=interact,
            msg=f"ConfirmDeleteView -> clicked yes",
        )
        try:
            await add_job(
                JobType.PARTY_DELETE,
                {"origin_msg": self.origin_message, "interact": interact},
            )
            await interact.client.trigger_queue_processing()
            await interact.edit_original_response(
                content=ts.get(f"{pf}delete-requested"), view=None
            )
        except Exception:
            await interact.followup.send(
                ts.get(f"{pf}del-err"), view=SupportView(), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd="btn.confirm.delete",
                interact=interact,
                msg=f"ConfirmDeleteView -> clicked yes | but ERR\n{return_traceback()}",
                obj=return_traceback(),
            )
        self.value = True
        self.stop()

    @ui.button(label=ts.get(f"{pf}del-btnn"), style=discord.ButtonStyle.secondary)
    async def no_button(self, interact: discord.Interaction, button: ui.Button):
        await interact.response.edit_message(
            content=ts.get(f"{pf}del-cancel"), view=None
        )
        self.value = False
        self.stop()

        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd="btn.confirm.delete.cancel",
            interact=interact,
            msg=f"ConfirmDeleteView -> clicked no",
        )


class KickMemberSelect(ui.Select):
    def __init__(self, members, original_message: discord.Message):
        self.original_message = original_message
        options = [
            discord.SelectOption(label=m["display_name"], value=str(m["user_id"]))
            for m in members
        ]
        super().__init__(
            placeholder=ts.get(f"{pf}pv-kick-modal-select-placeholder"),
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interact: discord.Interaction):
        await interact.response.edit_message(view=None)
        target_id = int(self.values[0])
        party, _ = await PartyService.get_party_by_message_id(
            interact.client.db, self.original_message.id
        )
        try:
            await PartyService.leave_participant(
                interact.client.db, party["id"], target_id
            )
            await add_job(JobType.PARTY_UPDATE, {"origin_msg": self.original_message})
            await interact.client.trigger_queue_processing()
            await self.original_message.channel.send(
                ts.get(f"{pf}pv-kick-success").format(name=f"<@{target_id}>")
            )
        except Exception as e:
            await interact.response.send_message(
                ts.get(f"{pf}pv-err-notfound"), view=SupportView(), ephemeral=True
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd="select.kick.member",
                interact=interact,
                msg=f"Kicked user {target_id} from party {party['id']}, but ERR {e}",
            )
            return

        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd="select.kick.member",
            interact=interact,
            msg=f"Kicked user {target_id} from party {party['id']}",
        )


class KickMemberView(ui.View):
    def __init__(self, members, original_message: discord.Message):
        super().__init__(timeout=60)
        self.add_item(KickMemberSelect(members, original_message))


# ----------------- Main View -----------------
class PartyView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cooldown_action = commands.CooldownMapping.from_cooldown(
            1, COOLDOWN_ACTION, commands.BucketType.user
        )
        self.cooldown_manage = commands.CooldownMapping.from_cooldown(
            1, COOLDOWN_SHORT, commands.BucketType.user
        )
        self.cooldown_call = commands.CooldownMapping.from_cooldown(
            1, COOLDOWN_BTN_CALL, commands.BucketType.user
        )

    @staticmethod
    async def check_permissions(
        interact: discord.Interaction,
        cooldown_action,
        check_host: bool = False,
        check_joined: bool = False,
        check_not_joined: bool = False,
        skip_banned: bool = False,
        cmd: str = "",
    ) -> bool | tuple[dict, dict]:
        if await is_cooldown(interact, cooldown_action):
            return False
        if not skip_banned and await is_banned_user(interact):
            return False
        if not await check_consent(interact):
            return False

        party, participants = await PartyService.get_party_by_message_id(
            interact.client.db, interact.message.id
        )
        if not await isPartyExist(interact, party):
            return False

        user_id = interact.user.id
        is_host: bool = user_id == party["host_id"]
        is_admin: bool = await is_admin_user(interact, notify=False, cmd=cmd)
        is_participant = any(p["user_id"] == user_id for p in participants)

        if check_host and not is_host:
            if not is_admin:
                await interact.response.send_message(
                    ts.get(f"{pf}pv-err-only-host"), ephemeral=True
                )
                return False

        if check_joined and interact.user.id == party["host_id"]:  # Host cannot leave
            await interact.response.send_message(
                ts.get(f"{pf}pv-host-exit-err"), ephemeral=True
            )
            return False
        if check_joined and not is_participant:
            await interact.response.send_message(
                ts.get(f"{pf}pv-already-left"), ephemeral=True
            )
            return False

        if check_not_joined and is_participant:
            await interact.response.send_message(
                ts.get(f"{pf}pv-already-joined"), ephemeral=True
            )
            return False
        return party, participants

    @ui.button(
        label=ts.get(f"{pf}pv-join-btn"),
        style=discord.ButtonStyle.success,
        custom_id="party_join",
        row=1,
    )
    async def join_party(self, interact: discord.Interaction, button: ui.Button):
        cmd = "PartyView.btn.join"
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd=cmd,
            interact=interact,
            msg=f"PartyView -> join_party",
        )
        #########################
        check_result = await self.check_permissions(
            interact, self.cooldown_action, check_not_joined=True, cmd=cmd
        )
        if not check_result:
            return

        party, participants = check_result

        if len(participants) >= party["max_users"]:
            await interact.response.send_message(ts.get(f"{pf}pv-full"), ephemeral=True)
            return

        view = ConfirmJoinLeaveView(
            action="join",
            party_id=party["id"],
            interact=interact,
            host_id=party["host_id"],
        )
        await interact.response.send_message(
            ts.get(f"{pf}pv-confirm-join"), view=view, ephemeral=True
        )

        timed_out = await view.wait()
        if timed_out:
            try:
                await interact.edit_original_response(
                    content=ts.get(f"{pf}pv-del-cancel"), view=None
                )
            except discord.errors.NotFound:
                pass

    @ui.button(
        label=ts.get(f"{pf}pv-leave-btn"),
        style=discord.ButtonStyle.danger,
        custom_id="party_leave",
        row=1,
    )
    async def leave_party(self, interact: discord.Interaction, button: ui.Button):
        cmd = "PartyView.btn.leave"
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd=cmd,
            interact=interact,
            msg=f"PartyView -> leave_party",
        )
        check_result = await self.check_permissions(
            interact, self.cooldown_action, check_joined=True, skip_banned=True, cmd=cmd
        )
        if not check_result:
            return

        party, participants = check_result

        view = ConfirmJoinLeaveView(
            action="leave",
            party_id=party["id"],
            interact=interact,
            host_id=party["host_id"],
        )
        await interact.response.send_message(
            ts.get(f"{pf}pv-confirm-exit"), view=view, ephemeral=True
        )

    @ui.button(
        label=ts.get(f"{pf}pv-mod-all"),
        style=discord.ButtonStyle.secondary,
        custom_id="party_edit_info",
        row=1,
    )
    async def edit_info(self, interact: discord.Interaction, button: ui.Button):
        cmd = "PartyView.btn.edit-info"
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd=cmd,
            interact=interact,
            msg=f"PartyView -> edit_info",
        )
        check_result = await self.check_permissions(
            interact, self.cooldown_manage, check_host=True, cmd=cmd
        )
        if not check_result:
            return

        party, participants = check_result

        await interact.response.send_modal(PartyEditAllModal(party, participants))

    @ui.button(
        label=ts.get(f"{pf}pv-done"),
        style=discord.ButtonStyle.primary,
        custom_id="party_toggle_close",
        row=2,
    )
    async def toggle_close(self, interact: discord.Interaction, button: ui.Button):
        cmd = "PartyView.btn.togle-close"
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd=cmd,
            interact=interact,
            msg=f"PartyView -> toggle_close",
        )
        check_result = await self.check_permissions(
            interact, self.cooldown_manage, check_host=True, cmd=cmd
        )
        if not check_result:
            return

        party, participants = check_result

        new_status = await PartyService.toggle_status(
            interact.client.db, party["id"], party["status"]
        )
        # UI Button Update
        is_done = new_status == ts.get(f"{pf}pv-done")
        button.label = ts.get(f"{pf}pv-ing") if is_done else ts.get(f"{pf}pv-done")
        button.style = (
            discord.ButtonStyle.success if is_done else discord.ButtonStyle.primary
        )
        # Disable/Enable other buttons
        for child in self.children:
            if child.custom_id in ["party_join"]:
                child.disabled = is_done

        await add_job(JobType.PARTY_TOGGLE, {"interact": interact, "view": self})
        await interact.client.trigger_queue_processing()
        await interact.response.send_message(
            f"**현재 모집 상태: {new_status}**\n" + ts.get(f"{pf}edit-requested"),
            ephemeral=True,
        )

    @ui.button(
        label=ts.get(f"{pf}pv-call-label"),
        style=discord.ButtonStyle.secondary,
        custom_id="party_call_members",
        row=2,
    )
    async def call_members(self, interact: discord.Interaction, button: ui.Button):
        cmd = "PartyView.btn.member-call"
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd=cmd,
            interact=interact,
            msg=f"PartyView -> call_members",
        )
        check_result = await self.check_permissions(
            interact, self.cooldown_call, check_host=True, cmd=cmd
        )
        if not check_result:
            return

        party, participants = check_result

        mentions = [
            p["user_mention"] for p in participants if p["user_id"] != party["host_id"]
        ]
        if not mentions:
            await interact.response.send_message(
                ts.get(f"{pf}pv-call-no-members"), ephemeral=True
            )
            return

        await interact.response.send_message(
            f"{' '.join(mentions)} {ts.get(f'{pf}pv-call-msg')}"
        )

    @ui.button(
        label=ts.get(f"{pf}pv-kick-label"),
        style=discord.ButtonStyle.secondary,
        custom_id="party_kick_member",
        row=2,
    )
    async def kick_member(self, interact: discord.Interaction, button: ui.Button):
        cmd = "PartyView.btn.member-kick"
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd=cmd,
            interact=interact,
            msg=f"PartyView -> kick_member",
        )
        check_result = await self.check_permissions(
            interact, self.cooldown_manage, check_host=True, cmd=cmd
        )
        if not check_result:
            return

        party, participants = check_result

        members_to_kick = [p for p in participants if p["user_id"] != party["host_id"]]
        if not members_to_kick:
            await interact.response.send_message(
                ts.get(f"{pf}pv-kick-no-members"), ephemeral=True
            )
            return

        await interact.response.send_message(
            ts.get(f"{pf}pv-kick-modal-title"),
            view=KickMemberView(members_to_kick, interact.message),
            ephemeral=True,
        )

    @ui.button(
        label=ts.get(f"{pf}pv-del-label"),
        style=discord.ButtonStyle.danger,
        custom_id="party_delete",
        row=2,
    )
    async def delete_party(self, interact: discord.Interaction, button: ui.Button):
        cmd = "PartyView.btn.delete-party"
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.event,
            cmd=cmd,
            interact=interact,
            msg=f"PartyView -> delete_party",
        )
        check_result = await self.check_permissions(
            interact, self.cooldown_manage, check_host=True, cmd=cmd
        )
        if not check_result:
            return

        view = ConfirmDeleteView(interact, interact.message, self)
        await interact.response.send_message(
            ts.get(f"{pf}pv-del-confirm"),
            view=view,
            ephemeral=True,
        )
