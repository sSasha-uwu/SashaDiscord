import secrets

from discord.ext import commands

from project.bots.bahamut.bot import BahamutBot
from project.common import update_emote_log


class CommandBahamut(commands.Cog):
    def __init__(self, bot: BahamutBot) -> None:
        self.bot = bot

    @commands.command(name="bahamut", help="get some dumb shit from bahamut")
    async def bahamut(self, ctx: commands.Context[commands.Bot]) -> None:
        selected_emoji = secrets.choice(list(self.bot.emotes.values()))
        update_emote_log(selected_emoji, "bahamut")
        await ctx.send(selected_emoji)


async def setup(bot: BahamutBot) -> None:
    await bot.add_cog(CommandBahamut(bot))
