import secrets

from discord.ext import commands

from project.bots.titan.bot import TitanBot


class CommandEightballtan(commands.Cog):
    def __init__(self, bot: TitanBot) -> None:
        self.bot = bot

    @commands.command(name="eightballtan", help="Have titan make decisions for you (be careful, he is evil).")
    async def eightballtan(self, ctx: commands.Context[commands.Bot]) -> None:
        titan_emotes = self.bot.emotes
        selected_emoji = secrets.choice([
            titan_emotes["yestan"],
            titan_emotes["notan"],
            "thonk",
            titan_emotes["doubtan"],
        ])
        if selected_emoji == "thonk":
            await ctx.send(
                secrets.choice([
                    titan_emotes["thinktan"],
                    titan_emotes["thonktan"],
                    titan_emotes["thonktanry"],
                ]),
            )
        await ctx.send(selected_emoji)


async def setup(bot: TitanBot) -> None:
    await bot.add_cog(CommandEightballtan(bot))
