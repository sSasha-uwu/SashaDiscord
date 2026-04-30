import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound  # pyright: ignore[reportMissingTypeStubs]

from bots.commands.titan import (
    eightballtan,
    stats,
    titan,
)
from project.common import TITAN_API_KEY, TITAN_ERROR_MESSAGE


def titan_bot() -> None:
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
        if isinstance(error, CommandNotFound):
            return
        await ctx.send(TITAN_ERROR_MESSAGE.format(error=error, cri=":criteetan:"))
        raise error

    @bot.event
    async def on_message(message: discord.Message) -> None:  # pyright: ignore[reportUnusedFunction]
        await bot.process_commands(message)

    bot.add_command(titan)
    bot.add_command(eightballtan)
    bot.add_command(stats)

    bot.run(TITAN_API_KEY)
