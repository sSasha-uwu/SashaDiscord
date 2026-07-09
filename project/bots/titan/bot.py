import time
from typing import Any, override

import discord
from discord.ext import commands

from project.common import TITAN_API_KEY, TITAN_COMMANDS, TITAN_ERROR_MESSAGE, TITAN_YAP_MESSAGE


class TitanBot(commands.Bot):
    is_yapping: bool = False
    emotes: dict[str, str]
    yap_start: float
    yap_end: float

    def __init__(self) -> None:
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.run(TITAN_API_KEY)
        self.emotes = {}

    async def on_ready(self) -> None:
        self.emotes = {emote.name: str(emote) for emote in self.emojis if "tan" in emote.name}
        print(f"Loaded {len(self.emotes)} emotes across {len(self.guilds)} guilds")

    async def on_guild_emojis_update(self, _guild: discord.Guild, _before: list[discord.Emoji], _after: list[discord.Emoji]) -> None:
        self.emotes = {emote.name: str(emote) for emote in self.emojis if "tan" in emote.name}
        print(f"Updated {len(self.emotes)} emotes across {len(self.guilds)} guilds")

    @override
    async def setup_hook(self) -> None:
        for command_file in TITAN_COMMANDS.glob("*.py"):
            await self.load_extension(f"project.bots.titan.commands.{command_file.stem}")

    @override
    async def on_command_error(
        self,
        context: commands.Context[Any],
        exception: commands.CommandError,
    ) -> None:
        if isinstance(exception, commands.CommandNotFound):
            return
        await context.send(TITAN_ERROR_MESSAGE.format(error=exception, explode=self.emotes.get("explodetan", "")))
        raise exception

    @override
    async def on_message(self, message: discord.Message) -> None:
        if self.is_yapping:
            self.yap_start = time.perf_counter()
        await self.process_commands(message)

    async def on_command_completion(self, _ctx: commands.Context[Any]) -> None:
        if self.is_yapping:
            self.yap_end = time.perf_counter()
            print(TITAN_YAP_MESSAGE.format(time=self.yap_end - self.yap_start))
