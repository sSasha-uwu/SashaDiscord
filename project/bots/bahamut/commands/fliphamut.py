import secrets

from discord.ext import commands

from project.bots.bahamut.bot import BahamutBot


class CommandFliphamut(commands.Cog):
    def __init__(self, bot: BahamutBot) -> None:
        self.bot = bot

    @commands.command(name="fliphamut", help="flip bahamut like a pancake (sometimes he lands on his side)")
    async def fliphamut(self, ctx: commands.Context[commands.Bot]) -> None:
        await ctx.send(
            secrets.choice(
                [self.bot.emotes["layhamut"], self.bot.emotes["bahamut"], self.bot.emotes["aushamut6"]],
            ),
        )


async def setup(bot: BahamutBot) -> None:
    await bot.add_cog(CommandFliphamut(bot))
