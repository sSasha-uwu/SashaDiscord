import operator
import secrets

from discord.ext import commands

from project.common import get_emote_log, get_titan_emotes, update_emote_log


@commands.command(name="titan")
async def titan(
    ctx: commands.Context[commands.Bot],
) -> None:
    titan_emotes = get_titan_emotes(ctx)
    selected_emoji = secrets.choice(list(titan_emotes.values()))
    update_emote_log(selected_emoji, "titan")
    await ctx.send(selected_emoji)


@commands.command(name="8balltan")
async def eightballtan(
    ctx: commands.Context[commands.Bot],
) -> None:
    titan_emotes = get_titan_emotes(ctx)
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


@commands.command(name="stats")
async def stats(
    ctx: commands.Context[commands.Bot],
) -> None:
    top_emotes = sorted(
        get_emote_log("titan").items(),
        key=operator.itemgetter(1),
        reverse=True,
    )[:5]
    await ctx.send(
        f"Top 5 titanisms:\n{'\n'.join(f'{emote}: {count}' for emote, count in top_emotes)}",
    )
