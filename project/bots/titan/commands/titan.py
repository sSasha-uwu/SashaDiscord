import secrets

from discord.ext import commands

from project.bots.titan.bot import TitanBot
from project.common import update_emote_log


class CommandTitan(commands.Cog):
    def __init__(self, bot: TitanBot) -> None:
        self.bot = bot

    @commands.command(name="titan", help="Shows a random titan emote.")
    async def titan(self, ctx: commands.Context[commands.Bot]) -> None:
        selected_emoji = secrets.choice(list(self.bot.emotes.values()))
        update_emote_log(selected_emoji, "titan")
        await ctx.send(selected_emoji)


async def setup(bot: TitanBot) -> None:
    await bot.add_cog(CommandTitan(bot))
