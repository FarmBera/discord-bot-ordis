import discord

from config.config import LOG_TYPE
from src.constants.notification import NOTI_LABELS, pfs, DB_COLUMN_MAP, pfu
from src.services.alert_service import fetch_current_subscriptions
from src.translator import ts
from src.utils.db_helper import transaction
from src.utils.logging_utils import save_log
from src.utils.return_err import return_traceback
from src.views.consent_view import check_consent
from src.views.help_view import SupportView


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
