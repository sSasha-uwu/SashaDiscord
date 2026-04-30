import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound  # pyright: ignore[reportMissingTypeStubs]

from bots.commands.titan import (
    eightballtan,
    stats,
    titan,
)
from project.common import TITAN_API_KEY, TITAN_ERROR_MESSAGE, titan_emotes


def titan_bot() -> None:
    bot = commands.Bot(
        command_prefix="!",
        intents=discord.Intents.all(),
        help_command=None,
    )

    print(len(bot.guilds))

    for guild in bot.guilds:
        for emoji in guild.emojis:
            emoji_raw = str(emoji)
            if "tan" in emoji_raw:
                emoji_str = emoji_raw.split(":")[1].split(":", maxsplit=1)[0]
                titan_emotes[emoji_str] = emoji_raw
                print(f"Loaded Titan emote: {emoji_str} -> {emoji_raw}")

    @bot.event
    async def on_command_error(  # pyright: ignore[reportUnusedFunction]
        ctx: commands.Context[commands.Bot],
        error: Exception,
    ) -> None:
        if isinstance(error, CommandNotFound):
            return
        await ctx.send(TITAN_ERROR_MESSAGE.format(error=error, cri=titan_emotes["criteetan"]))
        raise error

    @bot.event
    async def on_message(message: discord.Message) -> None:  # pyright: ignore[reportUnusedFunction]
        await bot.process_commands(message)

    bot.add_command(titan)
    bot.add_command(eightballtan)
    bot.add_command(stats)

    bot.run(TITAN_API_KEY)
