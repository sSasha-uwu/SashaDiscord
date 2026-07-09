import operator

from discord.ext import commands

from project.bots.titan.bot import TitanBot
from project.common import get_emote_log


class CommandStats(commands.Cog):
    def __init__(self, bot: TitanBot) -> None:
        self.bot = bot

    @commands.command(name="stats", help="Shows stats about titan emotes.")
    async def stats(self, ctx: commands.Context[commands.Bot]) -> None:
        top_emotes = sorted(
            get_emote_log("titan").items(),
            key=operator.itemgetter(1),
            reverse=True,
        )[:5]
        await ctx.send(
            f"Top 5 titanisms:\n{'\n'.join(f'{emote}: {count}' for emote, count in top_emotes)}",
        )


async def setup(bot: TitanBot) -> None:
    await bot.add_cog(CommandStats(bot))
