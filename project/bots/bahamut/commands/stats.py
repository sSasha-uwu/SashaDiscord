import operator

from discord.ext import commands

from project.bots.bahamut.bot import BahamutBot
from project.common import get_emote_log


class CommandStats(commands.Cog):
    def __init__(self, bot: BahamutBot) -> None:
        self.bot = bot

    @commands.command(name="stats", help="baha stats")
    async def stats(self, ctx: commands.Context[commands.Bot]) -> None:
        top_emotes = sorted(
            get_emote_log("bahamut").items(),
            key=operator.itemgetter(1),
            reverse=True,
        )[:5]
        await ctx.send(
            f"Top 5 bahamutisms:\n{'\n'.join(f'{emote}: {count}' for emote, count in top_emotes)}",
        )


async def setup(bot: BahamutBot) -> None:
    await bot.add_cog(CommandStats(bot))
