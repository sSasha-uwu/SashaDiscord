import secrets

from discord.ext import commands

from project.bots.bahamut.bot import BahamutBot


class CommandYaphamut(commands.Cog):
    def __init__(self, bot: BahamutBot) -> None:
        self.bot = bot

    @commands.command(name="yaphamut", help="makes bahamut spam debug shit in the console (sasha only)")
    @commands.is_owner()
    async def yaphamut(self, ctx: commands.Context[commands.Bot]) -> None:
        self.bot.is_yapping = not self.bot.is_yapping
        message = "shutting the fuck up"
        if self.bot.is_yapping:
            message = "yap" * (secrets.randbelow(5) + secrets.randbelow(5) + secrets.randbelow(5) + secrets.randbelow(5) + 1)
        await ctx.send(message)


async def setup(bot: BahamutBot) -> None:
    await bot.add_cog(CommandYaphamut(bot))
