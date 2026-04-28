#!/usr/bin/env python
# Copyright 2025
"""..."""

import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound  # pyright: ignore[reportMissingTypeStubs]

from bots.commands.titan import (
    eightballtan,
    stats,
    titan,
)
from project.common import BOT_ERROR_MESSAGE, TITAN_API_KEY


def titan_bot() -> None:
    """..."""
    bot = commands.Bot(
        command_prefix="!",
        intents=discord.Intents.all(),
        help_command=None,
    )

    @bot.event
    async def on_command_error(  # pyright: ignore[reportUnusedFunction]
        ctx: commands.Context[commands.Bot],
        error: Exception,
    ) -> None:
        """..."""
        if isinstance(error, CommandNotFound):
            return
        await ctx.send(BOT_ERROR_MESSAGE.format(error=error))
        raise error

    @bot.event
    async def on_message(message: discord.Message) -> None:  # pyright: ignore[reportUnusedFunction]
        """..."""
        await bot.process_commands(message)

    bot.add_command(titan)
    bot.add_command(eightballtan)
    bot.add_command(stats)

    bot.run(TITAN_API_KEY)
