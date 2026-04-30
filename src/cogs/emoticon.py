from typing import Callable

import discord
from discord import app_commands
from discord.ext import commands

from config.config import LOG_TYPE
from src.services.channel_service import ChannelService
from src.translator import ts
from src.utils.logging_utils import save_log
from src.utils.permission import is_banned_user
from src.views.consent_view import check_consent

# translation key prefix for this command
pf = "cmd.emoji."
pfa = "cmd.emoji-all."

# discord embed hard limits
_FIELD_VALUE_LIMIT = 1024
_DESCRIPTION_LIMIT = 4000
_EMBED_TOTAL_LIMIT = 6000
_EMBED_FIELD_LIMIT = 25
_MESSAGE_EMBED_LIMIT = 10


def _chunk_emojis(
    emojis: list[discord.Emoji],
    *,
    limit: int = _FIELD_VALUE_LIMIT,
    formatter: Callable[[discord.Emoji], str] = lambda e: f"{e} `:{e.name}:`\n",
) -> list[str]:
    """Pack emoji-formatted strings into chunks fitting a given char limit."""
    chunks: list[str] = []
    buf = ""
    for emoji in emojis:
        token = formatter(emoji)
        if len(buf) + len(token) > limit:
            chunks.append(buf.rstrip())
            buf = token
        else:
            buf += token
    if buf:
        chunks.append(buf.rstrip())
    return chunks


def build_embeds(guild: discord.Guild) -> list[discord.Embed]:
    """Build paginated embeds listing every emoji in the guild with names."""
    emojis = sorted(guild.emojis, key=lambda e: e.name.lower())
    static = [e for e in emojis if not e.animated]
    animated = [e for e in emojis if e.animated]

    head = discord.Embed(
        title=ts.get(f"{pf}title").format(guild=guild.name),
        description=ts.get(f"{pf}info").format(
            total=len(emojis),
            static=len(static),
            animated=len(animated),
        ),
        color=discord.Color.darker_gray(),
    )
    # if guild.icon:
    #     head.set_thumbnail(url=guild.icon.url)

    embeds: list[discord.Embed] = [head]

    def _attach(field_name: str, items: list[discord.Emoji]) -> None:
        if not items:
            return
        for idx, chunk in enumerate(_chunk_emojis(items)):
            target = embeds[-1]
            new_page = False
            # spawn a new embed if appending would exceed field count or total length
            if (
                len(target.fields) >= _EMBED_FIELD_LIMIT
                or len(target) + len(chunk) + len(field_name) > _EMBED_TOTAL_LIMIT
            ):
                target = discord.Embed(color=discord.Color.darker_gray())
                embeds.append(target)
                new_page = True
            # show the section label on the first chunk, or on a fresh embed
            name = field_name if (idx == 0 or new_page) else "\u200b"
            target.add_field(name=name, value=chunk, inline=False)

    _attach(ts.get(f"{pf}field-static"), static)
    _attach(ts.get(f"{pf}field-animated"), animated)
    return embeds


def _resolve_emoji(guild: discord.Guild, query: str) -> discord.Emoji | None:
    """Find a guild emoji by exact name, falling back to case-insensitive match."""
    exact = discord.utils.get(guild.emojis, name=query)
    if exact is not None:
        return exact
    needle = query.lower()
    return discord.utils.find(lambda e: e.name.lower() == needle, guild.emojis)


class EmojiCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="emoji", description=f"{pf}desc")
    @app_commands.describe(name=f"{pf}param-name")
    @discord.app_commands.checks.cooldown(1, 10, key=lambda i: (i.guild_id, i.user.id))
    async def cmd_show_emoji(self, interact: discord.Interaction, name: str) -> None:
        await interact.response.defer(ephemeral=True)

        if await is_banned_user(interact, isFollowUp=True):
            return
        if not await check_consent(interact):
            return

        # authorize the server
        channel_list = await ChannelService.getChannels(interact)
        if not channel_list:
            await interact.followup.send(ts.get("cmd.err-limit-server"), ephemeral=True)
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd="cmd.emoji",
                interact=interact,
                msg="cmd used, but unauthorized server",
            )
            return

        guild = interact.guild
        if guild is None:
            await interact.followup.send(ts.get(f"{pf}err-no-guild"), ephemeral=True)
            return

        emoji = _resolve_emoji(guild, name)
        if emoji is None:
            await interact.followup.send(
                ts.get(f"{pf}err-not-found").format(name=name),
                ephemeral=True,
            )
            return

        # use the member's role color
        # color = interact.user.color if interact.user.color.value else discord.Color.darker_gray()

        embed = discord.Embed(color=discord.Color.darker_gray())
        embed.set_author(
            name=interact.user.display_name,
            icon_url=interact.user.display_avatar.url,
        )
        embed.set_image(url=emoji.url)

        await interact.followup.send(embed=embed)
        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.cmd,
            cmd="cmd.emoji",
            interact=interact,
            msg=f"cmd used, displayed emoji :{emoji.name}:",
        )

    @cmd_show_emoji.autocomplete("name")
    async def _emoji_name_autocomplete(
        self,
        interact: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        guild = interact.guild
        if guild is None:
            return []

        matches = [e for e in guild.emojis if current.lower() in e.name.lower()]
        return [app_commands.Choice(name=e.name, value=e.name) for e in matches[:25]]

    @app_commands.command(name="emoji-all", description=f"{pfa}desc")
    @discord.app_commands.checks.cooldown(1, 30, key=lambda i: (i.guild_id, i.user.id))
    async def cmd_show_all_emojis(self, interact: discord.Interaction) -> None:
        # public response so the wall is visible to the channel
        await interact.response.defer(ephemeral=True)

        if await is_banned_user(interact, isFollowUp=True):
            return
        if not await check_consent(interact, isFollowUp=True):
            return

        # authorize the server
        channel_list = await ChannelService.getChannels(interact)
        if not channel_list:
            await interact.followup.send(ts.get("cmd.err-limit-server"), ephemeral=True)
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.err,
                cmd="cmd.emoji-all",
                interact=interact,
                msg="cmd used, but unauthorized server",
            )
            return

        guild = interact.guild
        if guild is None:
            await interact.followup.send(ts.get(f"{pf}err-no-guild"), ephemeral=True)
            return

        if not guild.emojis:
            await interact.followup.send(ts.get(f"{pf}err-empty"), ephemeral=True)
            await save_log(
                pool=interact.client.db,
                type=LOG_TYPE.cmd,
                cmd="cmd.emoji-all",
                interact=interact,
                msg="cmd used, but guild has no emojis",
            )
            return

        emojis = list(guild.emojis)
        static_count = sum(1 for e in emojis if not e.animated)
        animated_count = len(emojis) - static_count

        # check text length < 4000
        chunks = _chunk_emojis(
            emojis,
            limit=_DESCRIPTION_LIMIT,
            formatter=lambda e: f"{e}",
        )
        # title goes on the first embed, footer on the last embed
        last_idx = len(chunks) - 1
        for idx, chunk in enumerate(chunks):
            embed = discord.Embed(
                description=chunk,
                color=discord.Color.darker_gray(),
            )
            if idx == 0:
                embed.title = ts.get(f"{pf}title").format(total=len(emojis))
            if idx == last_idx:
                embed.set_footer(
                    text=ts.get(f"{pf}footer").format(
                        static=static_count,
                        animated=animated_count,
                    )
                )
            await interact.followup.send(embed=embed, ephemeral=True)

        await save_log(
            pool=interact.client.db,
            type=LOG_TYPE.cmd,
            cmd="cmd.emoji-all",
            interact=interact,
            msg=f"cmd used, displayed {len(emojis)} emojis in {len(chunks)} embeds",
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(EmojiCommands(bot))
