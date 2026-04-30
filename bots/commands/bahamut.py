import contextlib
import operator
import secrets
from pathlib import Path

import discord
from discord.ext import commands
from movielite import ImageClip, VideoClip, VideoWriter  # pyright: ignore[reportMissingTypeStubs]
from PIL import Image

from project.common import get_emote_log, hamut_emotes, update_emote_log


@commands.command(name="bahamut")
async def bahamut(ctx: commands.Context[commands.Bot]) -> None:
    if not hamut_emotes:
        for guild in ctx.bot.guilds:
            for emoji in guild.emojis:
                emoji_raw = str(emoji)
                if "hamut" in emoji_raw:
                    emoji_str = emoji_raw.split(":")[1].split(":", maxsplit=1)[0]
                    hamut_emotes[emoji_str] = emoji_raw
                    print(f"Loaded Bahamut emote: {emoji_str} -> {emoji_raw}")
    selected_emoji = secrets.choice(list(hamut_emotes.values()))
    update_emote_log(selected_emoji, "bahamut")
    await ctx.send(selected_emoji)


@commands.command(name="fliphamut")
async def fliphamut(ctx: commands.Context[commands.Bot]) -> None:
    await ctx.send(
        secrets.choice(
            [hamut_emotes["layhamut"], hamut_emotes["bahamut"], hamut_emotes["aushamut6"]],
        ),
    )


@commands.command(name="stats")
async def stats(ctx: commands.Context[commands.Bot]) -> None:
    top_emotes = sorted(
        get_emote_log("bahamut").items(),
        key=operator.itemgetter(1),
        reverse=True,
    )[:5]
    await ctx.send(
        f"Top 5 bahamutisms:\n{'\n'.join(f'{emote}: {count}' for emote, count in top_emotes)}",
    )


@commands.command(name="layhamut")
async def layhamut(ctx: commands.Context[commands.Bot]) -> None:
    if not ctx.message.attachments:
        await ctx.send("You didn't attach an image, you retard.")
        return

    image_path = Path(f"temp_image_{ctx.author.id}.png")
    output_path = Path(f"output_video_{ctx.author.id}.mp4")
    processed_image_path = Path(f"processed_image_{ctx.author.id}.png")

    await ctx.message.attachments[0].save(image_path)

    clip = VideoClip("bots/resources/layhamut/layhamut.mp4")
    fps = clip.fps
    frame_width, frame_height = clip.size

    # Image processing with PIL is identical — no changes needed here
    with Image.open(image_path) as img:
        img_aspect = img.width / img.height
        frame_aspect = frame_width / frame_height

        if img_aspect > frame_aspect:
            new_width = frame_width
            new_height = int(frame_width / img_aspect)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)  # noqa: PLW2901
            new_img = Image.new("RGB", (frame_width, frame_height), (0, 0, 0))
            new_img.paste(img, (0, (frame_height - new_height) // 2))
        else:
            new_height = frame_height
            new_width = int(frame_height * img_aspect)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)  # noqa: PLW2901
            new_img = Image.new("RGB", (frame_width, frame_height), (0, 0, 0))
            new_img.paste(img, ((frame_width - new_width) // 2, 0))

        new_img.save(processed_image_path)

    final_duration = clip.duration - 12 / fps

    # subclip(start, end) replaces clip[0:final_duration]
    video_segment = clip.subclip(0, final_duration)
    # Mute the segment's own (trimmed) audio so it doesn't overlap
    # with the full audio we add separately below
    video_segment.audio.set_volume(0)

    # Preserve original audio through the image frames (same intent as .with_audio())
    full_audio = clip.audio

    # start= replaces .with_start() — passed directly to the constructor
    image_clip = ImageClip(
        str(processed_image_path),
        start=final_duration,
        duration=12 / fps,
    )

    # VideoWriter + add_clips() replaces CompositeVideoClip + write_videofile()
    writer = VideoWriter(str(output_path), fps=fps, size=(frame_width, frame_height))
    writer.add_clips([video_segment, image_clip, full_audio])
    writer.write()

    clip.close()

    await ctx.message.delete()
    await ctx.send(file=discord.File(output_path))

    for file in [image_path, processed_image_path, output_path]:
        with contextlib.suppress(FileNotFoundError):
            file.unlink()
