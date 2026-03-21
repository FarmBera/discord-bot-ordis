import discord

from config.config import LOG_TYPE
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
)
from src.translator import ts
from src.utils.db_helper import transaction
from src.utils.logging_utils import save_log
from src.utils.return_err import return_traceback
from src.views.consent_view import check_consent
from src.views.help_view import SupportView

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


async def fetch_current_subscriptions(db, channel_id: int) -> list:
    """
    get the current list of notifications subscribed to interacted channel from the db.
    """
    active_labels = []
    cols = list(DB_COLUMN_MAP.values())
    # column name mapping
    col_to_key = {v: k for k, v in DB_COLUMN_MAP.items()}

    query = f"SELECT {', '.join(cols)} FROM webhooks WHERE channel_id = %s"
    try:
        async with transaction(db) as cursor:
            await cursor.execute(query, (channel_id,))
            row = await cursor.fetchone()

        if row:
            for col_name in cols:
                val = row[col_name]

                if val == 1:
                    key = col_to_key.get(col_name)
                    # convert labels
                    if key and key in NOTI_LABELS:
                        active_labels.append(NOTI_LABELS[key])
    except Exception as e:
        await save_log(
            pool=db,
            type=LOG_TYPE.cmd,
            cmd="fetch_current_subscriptions",
            msg="db select error",  # VAR
            obj=return_traceback(),
        )
        print(f"[Error] fetch_current_subscriptions: {e}")

    return active_labels


class NotificationSelect(discord.ui.Select):
    def __init__(self):
        options = []
        # create options
        for key, label in NOTI_LABELS.items():
            options.append(discord.SelectOption(label=label, value=key))

        super().__init__(
            placeholder=ts.get(f"{pfs}select-placeholder"),
            min_values=0,
            max_values=len(NOTI_LABELS),
            options=options,
        )

    async def on_error(
        self, interact: discord.Interaction, error: Exception, item: discord.ui.Item
    ) -> None:
        await interact.edit_original_response(
            content=ts.get(f"general.error-cmd"), embed=None, view=None
        )
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.cmd,
            cmd=f"{LOG_TYPE.cmd}.set-noti-insert",
            interact=interact,
            msg=f"error: {error}",
            obj=f"{self.values}\n{item}\n{return_traceback()}",
        )

    async def callback(self, interact: discord.Interaction):
        await interact.response.defer(ephemeral=True)

        # check permission
        if not interact.channel.permissions_for(interact.guild.me).manage_webhooks:
            await interact.edit_original_response(
                content=ts.get("cmd.err-perm-webhook"),
                embed=None,
                view=None,
            )
            return

        # get/create webhook
        bot_name = interact.client.user.display_name
        webhooks = await interact.channel.webhooks()
        webhook = discord.utils.get(webhooks, name=bot_name)
        if not webhook:
            try:
                # get bot avatar
                avatar_bytes = None
                if interact.client.user.avatar:
                    avatar_bytes = await interact.client.user.avatar.read()

                webhook = await interact.channel.create_webhook(
                    name=bot_name, avatar=avatar_bytes
                )
            except Exception:
                webhook = await interact.channel.create_webhook(name=bot_name)

        # create sql query
        sql_base = "INSERT INTO webhooks (channel_id, guild_id, webhook_url, note, {cols}) VALUES (%s, %s, %s, %s, {vals}) ON DUPLICATE KEY UPDATE webhook_url=%s{updates}"
        col_names = []
        val_placeholders = []
        update_clauses = []
        insert_values = [
            interact.channel_id,
            interact.guild_id,
            webhook.url,
            f"{interact.guild.name}/{interact.channel.name}",
        ]
        update_values = [webhook.url]

        for key, col_name in DB_COLUMN_MAP.items():
            is_selected = 1 if str(key) in self.values else 0

            col_names.append(col_name)
            val_placeholders.append("%s")
            insert_values.append(is_selected)

            if is_selected:
                update_clauses.append(f"{col_name}=%s")
                update_values.append(is_selected)

        updates_sql = ""
        if update_clauses:
            updates_sql = ", " + ", ".join(update_clauses)

        final_sql = sql_base.format(
            cols=", ".join(col_names),
            vals=", ".join(val_placeholders),
            updates=updates_sql,
        )

        # send sql query
        try:
            async with transaction(interact.client.db) as cursor:
                await cursor.execute(final_sql, insert_values + update_values)
        except Exception:
            await interact.edit_original_response(
                content=ts.get(f"cmd.err-db"), embed=None, view=SupportView()
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.cmd,
                cmd=f"{LOG_TYPE.cmd}.set-noti",
                interact=interact,
                msg="db error",  # VAR
                obj=return_traceback(),
            )
            return

        # display current subscription status
        current_subs = await fetch_current_subscriptions(
            interact.client.db, interact.channel_id
        )
        subs_str = ", ".join(current_subs) if current_subs else ts.get("cmd.alert.none")

        await interact.edit_original_response(
            content=ts.get(f"{pfs}done").format(count=len(self.values))
            + ts.get("cmd.alert.current").format(sub_list=subs_str),
            embed=None,
            view=None,
        )
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.cmd,
            cmd=f"{LOG_TYPE.cmd}.set-noti-insert",
            interact=interact,
            msg="successfully inserted",
            obj=f"{self.values}",
        )


class NotificationUnSelect(discord.ui.Select):
    def __init__(self):
        options = []
        # create options
        for key, label in NOTI_LABELS.items():
            options.append(discord.SelectOption(label=label, value=str(key)))

        super().__init__(
            placeholder=ts.get(f"{pfu}select-placeholder"),
            min_values=1,  # select at least one
            max_values=len(NOTI_LABELS),
            options=options,
        )

    async def on_error(
        self, interact: discord.Interaction, error: Exception, item: discord.ui.Item
    ) -> None:
        await interact.edit_original_response(
            content=ts.get(f"general.error-cmd"), embed=None, view=None
        )
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.cmd,
            cmd=f"{LOG_TYPE.cmd}.set-noti-insert",
            interact=interact,
            msg="unknown error",
            obj=f"{self.values}\n{return_traceback()}",
        )

    async def callback(self, interact: discord.Interaction):
        await interact.response.defer(ephemeral=True)

        # check permission
        if not interact.channel.permissions_for(interact.guild.me).manage_webhooks:
            await interact.edit_original_response(
                content=ts.get("cmd.err-perm-webhook"),
                embed=None,
                view=None,
            )
            return

        db_pool = interact.client.db
        is_fully_deleted = False

        # unsubscribe selected alert
        if self.values:
            set_clauses = []
            for val in self.values:
                target_col = None
                for k, col in DB_COLUMN_MAP.items():
                    if str(k) == val:
                        target_col = col
                        break

                if target_col:
                    set_clauses.append(f"{target_col} = 0")

            if set_clauses:
                sql_update = f"UPDATE webhooks SET {', '.join(set_clauses)} WHERE channel_id = %s"
                async with transaction(db_pool) as cursor:
                    await cursor.execute(sql_update, (interact.channel_id,))

        # verify all notifications are turned off (DELETE)
        all_columns = list(DB_COLUMN_MAP.values())
        where_conditions = " AND ".join([f"{col}=0" for col in all_columns])
        # delete where alert flag is 0
        sql_delete = (
            f"DELETE FROM webhooks WHERE channel_id = %s AND {where_conditions}"
        )
        try:
            async with transaction(db_pool) as cursor:
                await cursor.execute(sql_delete, (interact.channel_id,))

                if cursor.rowcount > 0:
                    is_fully_deleted = True
        except Exception:
            await interact.edit_original_response(
                content=ts.get(f"cmd.err-db"), embed=None, view=SupportView()
            )
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.cmd,
                cmd=f"{LOG_TYPE.cmd}.delete-noti",
                interact=interact,
                msg="db error",
                obj=return_traceback(),
            )
            return

        # send msg
        msg = ts.get(f"{pfu}done").format(count=len(self.values))

        if is_fully_deleted:
            try:
                webhooks = await interact.channel.webhooks()
                webhook = discord.utils.get(
                    webhooks, name=interact.client.user.display_name
                )
                if webhook:
                    await webhook.delete(reason=ts.get(f"{pfu}reason"))
            except:
                pass
            # notify all alert is removed
            msg += ts.get(f"{pfu}all-unsub")
        else:
            # display remain subscriptions
            current_subs = await fetch_current_subscriptions(
                interact.client.db, interact.channel_id
            )
            subs_str = (
                ", ".join(current_subs) if current_subs else ts.get("cmd.alert.none")
            )
            msg += ts.get("cmd.alert.current").format(sub_list=subs_str)

        await interact.edit_original_response(content=msg, embed=None, view=None)
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.cmd,
            cmd=f"{LOG_TYPE.cmd}.delete-noti",
            interact=interact,
            msg="successfully deleted",
            obj=f"{self.values}",
        )


class SettingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(NotificationSelect())


class UnSettingView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        self.add_item(NotificationUnSelect())


async def noti_subscribe_helper(interact: discord.Interaction):
    await interact.response.defer(ephemeral=True)
    if not await check_consent(interact, isFollowUp=True):
        return

    current_subs = await fetch_current_subscriptions(
        interact.client.db, interact.channel_id
    )
    subs_str = ", ".join(current_subs) if current_subs else ts.get(f"cmd.alert.none")

    await interact.followup.send(
        content=ts.get(f"{pfs}select-msg")
        + ts.get("cmd.alert.current").format(sub_list=subs_str),
        view=SettingView(),
        ephemeral=True,
    )
    await save_log(
        pool=interact.client.db,
        type=LOG_TYPE.cmd,
        cmd=f"{LOG_TYPE.cmd}.set-noti",
        interact=interact,
        msg="cmd used",
    )


async def noti_unsubscribe_helper(interact: discord.Interaction):
    await interact.response.defer(ephemeral=True)
    if not await check_consent(interact, isFollowUp=True):
        return

    current_subs = await fetch_current_subscriptions(
        interact.client.db, interact.channel_id
    )
    subs_str = ", ".join(current_subs) if current_subs else ts.get(f"cmd.alert.none")

    await interact.followup.send(
        content=ts.get(f"{pfu}select-msg")
        + ts.get("cmd.alert.current").format(sub_list=subs_str),
        view=UnSettingView(),
        ephemeral=True,
    )
    await save_log(
        pool=interact.client.db,
        type=LOG_TYPE.cmd,
        cmd=f"{LOG_TYPE.cmd}.delete-noti",
        interact=interact,
        msg="cmd used",
    )
