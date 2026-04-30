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
from project.common import BAHAMUT_API_KEY, BAHAMUT_ERROR_MESSAGE, hamut_emotes


async def bahamut_bot() -> None:
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
        await ctx.send(BAHAMUT_ERROR_MESSAGE.format(error=error, explode="explodehamut"))
        raise error

    @bot.event
    async def on_message(message: discord.Message) -> None:  # pyright: ignore[reportUnusedFunction]
        await bot.process_commands(message)

    bot.add_command(bahamut)
    bot.add_command(fliphamut)
    bot.add_command(layhamut)
    bot.add_command(stats)

    await bot.start(BAHAMUT_API_KEY)

    for guild in bot.guilds:
        for emoji in guild.emojis:
            emoji_raw = str(emoji)
            if "hamut" in emoji_raw:
                emoji_str = emoji_raw.split(":")[1].split(":", maxsplit=1)[0]
                hamut_emotes[emoji_str] = emoji_raw
                print(f"Loaded Bahamut emote: {emoji_str} -> {emoji_raw}")
