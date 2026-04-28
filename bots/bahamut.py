#!/usr/bin/env python
# Copyright 2025
"""..."""

import discord
from discord.ext import commands
from discord.ext.commands import (  # pyright: ignore[reportMissingTypeStubs]
    CommandNotFound,
)

from bots.commands.bahamut import (
    bahamut,
    fliphamut,
    layhamut,
    stats,
)
from project.common import BAHAMUT_API_KEY, BOT_ERROR_MESSAGE


def bahamut_bot() -> None:
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

    bot.add_command(bahamut)
    bot.add_command(fliphamut)
    bot.add_command(layhamut)
    bot.add_command(stats)

    bot.run(BAHAMUT_API_KEY)
