import time
from typing import Any, override

import discord
from discord.ext import commands

from project.common import BAHAMUT_API_KEY, BAHAMUT_COMMANDS, BAHAMUT_ERROR_MESSAGE, BAHAMUT_YAP_MESSAGE


class BahamutBot(commands.Bot):
    is_yapping: bool = False
    emotes: dict[str, str]
    yap_start: float = 0
    yap_end: float = 0

    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.run(BAHAMUT_API_KEY)
        self.emotes = {}

    async def on_ready(self) -> None:
        self.emotes = {emote.name: str(emote) for emote in self.emojis if "hamut" in emote.name}
        print(f"Loaded {len(self.emotes)} emotes across {len(self.guilds)} guilds")

    async def on_guild_emojis_update(self, _guild: discord.Guild, _before: list[discord.Emoji], _after: list[discord.Emoji]) -> None:
        self.emotes = {emote.name: str(emote) for emote in self.emojis if "hamut" in emote.name}
        print(f"Updated emotes across {len(self.guilds)} guilds")

    @override
    async def setup_hook(self) -> None:
        for command_file in BAHAMUT_COMMANDS.glob("*.py"):
            await self.load_extension(f"project.bots.bahamut.commands.{command_file.stem}")

    @override
    async def on_command_error(
        self,
        context: commands.Context[Any],
        exception: commands.CommandError,
    ) -> None:
        if isinstance(exception, commands.CommandNotFound):
            return
        if len(str(exception)) > 1500:
            exception = commands.CommandError("Error message too long to display")
        await context.send(BAHAMUT_ERROR_MESSAGE.format(error=exception, explode=self.emotes.get("explodehamut", "")))
        raise exception

    @override
    async def on_message(self, message: discord.Message) -> None:
        if self.is_yapping and not message.author.bot:
            self.yap_start = time.perf_counter()
            print(self.yap_start)
        await self.process_commands(message)

    async def on_command_completion(self, _ctx: commands.Context[Any]) -> None:
        if self.is_yapping and self.yap_start != 0:
            self.yap_end = time.perf_counter()
            print(BAHAMUT_YAP_MESSAGE.format(time=self.yap_end - self.yap_start))
