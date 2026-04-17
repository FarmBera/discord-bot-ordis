import discord

from src.constants.keys import LFG_WEBHOOK_NAME
from src.utils.delay import delay

# Per-channel webhook cache: channel_id -> Webhook
WEBHOOK_CACHE: dict[int, discord.Webhook] = {}


async def get_webhook(target_channel, avatar) -> discord.Webhook:
    """
    Return a cached webhook for the given channel.
    Only calls the Discord API on cache miss.
    """
    channel_id = target_channel.id

    cached = WEBHOOK_CACHE.get(channel_id)
    if cached:
        return cached

    webhook_list = await target_channel.webhooks()
    webhook = discord.utils.get(webhook_list, name=LFG_WEBHOOK_NAME)

    if not webhook:
        avatar_byte = await avatar.read()
        webhook = await target_channel.create_webhook(
            name=LFG_WEBHOOK_NAME, avatar=avatar_byte
        )

    WEBHOOK_CACHE[channel_id] = webhook
    await delay()
    return webhook


def invalidate_webhook(channel_id: int):
    """Invalidate the cached webhook for a given channel."""
    WEBHOOK_CACHE.pop(channel_id, None)


async def webhook_send(target_channel, avatar, **kwargs) -> discord.WebhookMessage:
    """
    Send a message via webhook.
    Automatically invalidates cache and retries if the cached webhook was deleted.
    """
    webhook = await get_webhook(target_channel, avatar)
    try:
        return await webhook.send(**kwargs)
    except discord.NotFound:
        invalidate_webhook(target_channel.id)
        webhook = await get_webhook(target_channel, avatar)
        return await webhook.send(**kwargs)


async def webhook_edit(target_channel, avatar, message_id: int, **kwargs) -> bool:
    """
    Edit a message sent via webhook.
    Returns True on success, False if the message or webhook was not found.
    """
    webhook = await get_webhook(target_channel, avatar)
    try:
        await webhook.edit_message(message_id=message_id, **kwargs)
        return True
    except discord.NotFound:
        return False
        # retry fetch webhook
        invalidate_webhook(target_channel.id)
        try:
            webhook = await get_webhook(target_channel, avatar)
            await webhook.edit_message(message_id=message_id, **kwargs)
            return True
        except discord.NotFound:
            return False
