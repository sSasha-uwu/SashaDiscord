#!/usr/bin/env python
# Copyright 2025
"""..."""

import operator
import secrets

from discord.ext import commands

from project.common import get_emote_log, update_emote_log


@commands.command(name="titan")
async def titan(
    ctx: commands.Context[commands.Bot],
) -> None:
    """..."""
    emojis: list[str] = []
    for guild in ctx.bot.guilds:
        emojis.extend(str(emoji) for emoji in guild.emojis)

    titan_emojis = [emoji for emoji in emojis if "tan" in emoji]

    selected_emoji = secrets.choice(titan_emojis)
    update_emote_log(selected_emoji, "titan")
    await ctx.send(selected_emoji)


@commands.command(name="8balltan")
async def eightballtan(
    ctx: commands.Context[commands.Bot],
) -> None:
    """..."""
    eightball_emojis: list[str] = [
        "<:yestan:608551635844857856>",
        "<:notan:612894048990003200>",
        "thonk",
        "<:doubtan:637821087987662856>",
    ]
    thonk_emojis: list[str] = [
        "<:thinktan:610471993619382328>",
        "<:thonktan:610474371672178713>",
        "<:thonktanry:610474396200599552>",
    ]
    selected_emoji = secrets.choice(eightball_emojis)
    if selected_emoji == "thonk":
        await ctx.send(secrets.choice(thonk_emojis))
    await ctx.send(selected_emoji)
    await ctx.send("good job it works, only took like 30 minutes you idiot")


@commands.command(name="stats")
async def stats(
    ctx: commands.Context[commands.Bot],
) -> None:
    """..."""
    top_emotes = sorted(
        get_emote_log("titan").items(),
        key=operator.itemgetter(1),
        reverse=True,
    )[:5]
    await ctx.send(
        f"Top 5 titanisms:\n{'\n'.join(f'{emote}: {count}' for emote, count in top_emotes)}",
    )
