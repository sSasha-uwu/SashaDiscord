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
    wheelhamut,
)
from project.common import BAHAMUT_API_KEY, BAHAMUT_ERROR_MESSAGE, get_hamut_emotes


def bahamut_bot() -> None:
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
        hamut_emotes = get_hamut_emotes(ctx)
        await ctx.send(BAHAMUT_ERROR_MESSAGE.format(error=error, explode=hamut_emotes["explodehamut"] or ""))
        raise error

    @bot.event
    async def on_message(message: discord.Message) -> None:  # pyright: ignore[reportUnusedFunction]
        await bot.process_commands(message)

    bot.add_command(bahamut)
    bot.add_command(fliphamut)
    bot.add_command(layhamut)
    bot.add_command(stats)
    bot.add_command(wheelhamut)

    bot.run(BAHAMUT_API_KEY)
