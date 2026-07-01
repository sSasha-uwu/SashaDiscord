import contextlib
import math
import operator
import random
import secrets
import subprocess
from pathlib import Path

import cv2
import discord
import numpy as np
from discord.ext import commands
from movielite import ImageClip, VideoClip, VideoWriter  # pyright: ignore[reportMissingTypeStubs]
from PIL import Image, ImageDraw, ImageFont

from project.common import get_emote_log, get_hamut_emotes, update_emote_log


@commands.command(name="bahamut")
async def bahamut(ctx: commands.Context[commands.Bot]) -> None:
    hamut_emotes = get_hamut_emotes(ctx)
    selected_emoji = secrets.choice(list(hamut_emotes.values()))
    update_emote_log(selected_emoji, "bahamut")
    await ctx.send(selected_emoji)


@commands.command(name="fliphamut")
async def fliphamut(ctx: commands.Context[commands.Bot]) -> None:
    hamut_emotes = get_hamut_emotes(ctx)
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


@commands.command(name="wheelhamut")
async def wheelhamut(ctx: commands.Context[commands.Bot]) -> None:
    # get message text from command

    def draw_wheel(names: list[str], angle_offset: float, size: int, radius: int) -> Image.Image:
        """Return a PIL RGBA image of the wheel rotated by angle_offset (degrees)."""
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cx, cy = size // 2, size // 2
        n = len(names)
        slice_deg = 360.0 / n

        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
            font_hires = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size * scale)
        except OSError:
            font = ImageFont.load_default(font_size)
            font_hires = font

        for i, name in enumerate(names):
            start_angle = angle_offset + i * slice_deg
            end_angle = start_angle + slice_deg
            color = palette[i % len(palette)]

            bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
            draw.pieslice(bbox, start=start_angle, end=end_angle, fill=color, outline="white")

            mid_angle_rad = math.radians(start_angle + slice_deg / 2)
            tx = cx + radius * 0.65 * math.cos(mid_angle_rad)
            ty = cy + radius * 0.65 * math.sin(mid_angle_rad)

            text_rotation = (start_angle + slice_deg / 2) % 360

            if 90 < text_rotation < 270:  # noqa: PLR2004
                text_rotation += 180

            bbox_hires = font_hires.getbbox(name)
            canvas_w = int((bbox_hires[2] - bbox_hires[0]) + pad * 2)
            canvas_h = int((bbox_hires[3] - bbox_hires[1]) + pad * 2)
            txt_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            txt_draw = ImageDraw.Draw(txt_img)
            txt_draw.text(
                (pad - bbox_hires[0], pad - bbox_hires[1]),
                name,
                font=font_hires,
                fill="white",
            )
            txt_img = txt_img.rotate(-text_rotation, expand=True, resample=Image.Resampling.BICUBIC)
            txt_img = txt_img.resize(
                (txt_img.width // scale, txt_img.height // scale),
                Image.Resampling.LANCZOS,
            )

            paste_x = int(tx - txt_img.width / 2)
            paste_y = int(ty - txt_img.height / 2)
            img.paste(txt_img, (paste_x, paste_y), txt_img)

        # Draw border circle
        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline="white", width=4)
        # Draw centre hub
        hub_r = 18
        draw.ellipse([cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r], fill="white", outline="#cccccc", width=2)

        return img

    def load_pin(pin_path: str, size: int) -> Image.Image:
        """Load the pin image, resize it, and ensure it has an alpha channel."""
        pin = Image.open(pin_path).convert("RGBA")
        return pin.resize((size, size), Image.Resampling.LANCZOS)

    def ease_out_cubic(t: float) -> float:
        """Ease-out cubic: starts fast, decelerates to a stop."""
        return 1 - (1 - t) ** 3

    message_text = ctx.message.content.removeprefix("!wheelhamut")
    names = message_text.split(",")
    pin_path = "bots/resources/wheelhamut/wheelhamut.png"
    output_path = "wheelhamut_result.mp4"
    video_size = 800  # Width and height of the output video (square)
    wheel_radius = 320  # Radius of the wheel in pixels
    video_fps = 24  # Frames per second
    spin_seconds = 5  # Total duration of the spin animation
    font_size = 56  # Font size for segment labels
    pin_size = 100  # Pin image will be scaled to this size (square)
    scale = 2
    pad = 12 * scale
    # Palette — segments cycle through these colours
    palette = [
        "#E63946",
        "#F4A261",
        "#2A9D8F",
        "#457B9D",
        "#8338EC",
        "#FB5607",
        "#3A86FF",
        "#06D6A0",
        "#FFBE0B",
        "#FF006E",
        "#8AC926",
        "#6A4C93",
    ]
    if not names:
        raise ValueError("What am I supposed to put on the wheel you dumb fuck?")

    n = len(names)
    slice_deg = 360.0 / n
    total_frames = video_fps * spin_seconds
    size = video_size

    winner_index = random.randint(0, n - 1)  # noqa: S311
    winner_index = winner_index % n
    winner_name = names[winner_index]

    # The pin sits at the top-centre (90° in standard PIL coordinates,
    # which treats 0° as 3 o'clock and goes clockwise).
    # We want the winning segment centred at 90° at the end of the spin.
    # The centre of the winning segment starts at:
    #   initial_offset + winner_index * slice_deg + slice_deg/2
    # We want that to equal 90°, so:
    pin_angle = 90.0
    winning_centre_at_zero = winner_index * slice_deg + slice_deg / 2
    extra_spins = random.randint(5, 8) * 360  # noqa: S311
    # Normalise so we always spin forward (negative = clockwise in PIL)
    # We'll pass angle_offset directly; PIL's pieslice uses clockwise degrees.

    start_offset = 0.0
    total_rotation = extra_spins + (pin_angle - winning_centre_at_zero - start_offset) % 360

    # Load assets
    pin_img = load_pin(pin_path, pin_size)

    # Composite background colour
    bg_color = (30, 30, 30)

    print("test")

    # Set up ffmpeg process instead of cv2.VideoWriter
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-s",
        f"{size}x{size}",
        "-pix_fmt",
        "bgr24",
        "-r",
        str(video_fps),
        "-i",
        "-",
        "-c:v",
        "h264_v4l2m2m",  # hardware encoder — swap to libx264 if unavailable
        "-b:v",
        "4M",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        output_path,
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.PIPE)

    print("test2")

    print(f"Rendering {total_frames} frames → winner: '{winner_name}' (index {winner_index})")

    frame_bgr = None
    for frame_idx in range(total_frames):
        t = frame_idx / (total_frames - 1)  # 0.0 → 1.0
        eased = ease_out_cubic(t)
        current_rotation = eased * total_rotation  # degrees rotated so far

        angle_offset = start_offset - current_rotation  # subtract = clockwise spin

        # Draw wheel
        wheel = draw_wheel(names, angle_offset, size, wheel_radius)

        # Composite onto background
        bg = Image.new("RGBA", (size, size), (*bg_color, 255))
        bg.paste(wheel, (0, 0), wheel)

        # Paste pin at top-centre
        pin_x = size // 2 - pin_size // 2
        pin_y = 660  # top edge; adjust if your pin image has its point at the bottom
        bg.paste(pin_img, (pin_x, pin_y), pin_img)

        # Convert to BGR for ffmpeg
        frame_np = np.array(bg.convert("RGB"))
        frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
        proc.stdin.write(frame_bgr.astype(np.uint8).tobytes())

        if frame_idx % video_fps == 0:
            print(f"  Frame {frame_idx}/{total_frames} ({int(t * 100)}%)")

    # Hold final frame for 2 seconds
    hold_frames = video_fps * 2

    if frame_bgr is not None:
        for _ in range(hold_frames):
            proc.stdin.write(frame_bgr.astype(np.uint8).tobytes())
    else:
        raise RuntimeError("I fucked up my soup.")

    proc.stdin.close()
    proc.wait()

    await ctx.send(file=discord.File(output_path))

    with contextlib.suppress(FileNotFoundError):
        Path(output_path).unlink()  # noqa: ASYNC240
