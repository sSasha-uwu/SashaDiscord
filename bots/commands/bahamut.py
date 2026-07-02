import asyncio
import contextlib
import json
import math
import operator
import random
import secrets
import shutil
import subprocess
import tempfile
from functools import partial
from pathlib import Path

import cv2
import discord
import numpy as np
from discord.ext import commands
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
        await ctx.send("You didn't attach an image.")
        return

    image_path = Path(f"temp_image_{ctx.author.id}.png")
    output_path = Path(f"output_video_{ctx.author.id}.webm")
    processed_image_path = Path(f"processed_image_{ctx.author.id}.png")

    await ctx.message.attachments[0].save(image_path)
    # Use ffprobe to get source video properties (fast) and offload
    # heavy ffmpeg work to a thread to keep the event loop responsive.
    base_video = Path("bots/resources/layhamut/layhamut.mp4")

    def ffprobe_info(path: Path) -> tuple[int, int, float, float]:
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height,r_frame_rate",
            "-show_entries",
            "format=duration",
            "-print_format",
            "json",
            str(path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        stream = data["streams"][0]
        width = int(stream["width"])
        height = int(stream["height"])
        rfr = stream.get("r_frame_rate", "25/1")
        num, den = map(int, rfr.split("/"))
        fps = num / den if den else 25.0
        duration = float(data["format"]["duration"]) if "format" in data and "duration" in data["format"] else 0.0
        return width, height, fps, duration

    # Small semaphore to avoid overloading the Pi with concurrent ffmpeg jobs
    try:
        PROCESS_SEMAPHORE
    except NameError:
        PROCESS_SEMAPHORE = asyncio.Semaphore(1)

    src_w, src_h, src_fps, src_dur = ffprobe_info(base_video)

    # Target parameters tuned for Raspberry Pi Zero 2 W
    target_fps = min(int(round(src_fps)), 15)
    max_width = 480
    if src_w > max_width:
        target_w = max_width
        target_h = int(src_h * (max_width / src_w))
    else:
        target_w, target_h = src_w, src_h

    img_dur = 12 / src_fps
    final_duration = max(0.5, src_dur - img_dur)

    # Resize/pad the uploaded image to the target frame size to avoid ffmpeg doing heavy per-frame scaling
    with Image.open(image_path) as img:
        img_aspect = img.width / img.height
        frame_aspect = target_w / target_h

        if img_aspect > frame_aspect:
            new_width = target_w
            new_height = int(target_w / img_aspect)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)  # noqa: PLW2901
            new_img = Image.new("RGB", (target_w, target_h), (0, 0, 0))
            new_img.paste(img, (0, (target_h - new_height) // 2))
        else:
            new_height = target_h
            new_width = int(target_h * img_aspect)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)  # noqa: PLW2901
            new_img = Image.new("RGB", (target_w, target_h), (0, 0, 0))
            new_img.paste(img, ((target_w - new_width) // 2, 0))

        new_img.save(processed_image_path)

    def process_work() -> None:
        tmpdir = tempfile.mkdtemp(prefix="layhamut_")
        try:
            image_clip = Path(tmpdir) / "image_clip.webm"
            trimmed = Path(tmpdir) / "trimmed.webm"

            # 1) Create short image clip from the processed image
            # Use VP8 for WebM output with fast settings for Pi
            cmd_img = [
                "ffmpeg",
                "-y",
                "-loop",
                "1",
                "-i",
                str(processed_image_path),
                "-t",
                str(img_dur),
                "-r",
                str(target_fps),
                "-c:v",
                "libvpx",
                "-cpu-used",
                "5",
                "-crf",
                "40",
                "-b:v",
                "0",
                "-pix_fmt",
                "yuv420p",
                str(image_clip),
            ]
            subprocess.run(cmd_img, check=True)

            # 2) Trim the base video to final_duration (video only)
            cmd_trim = [
                "ffmpeg",
                "-y",
                "-ss",
                "0",
                "-i",
                str(base_video),
                "-t",
                str(final_duration),
                "-r",
                str(target_fps),
                "-vf",
                f"scale={target_w}:{target_h}",
                "-c:v",
                "libvpx",
                "-cpu-used",
                "5",
                "-crf",
                "40",
                "-b:v",
                "0",
                "-pix_fmt",
                "yuv420p",
                "-an",
                str(trimmed),
            ]
            subprocess.run(cmd_trim, check=True)

            # 3) Concat trimmed video + image clip, map original audio from base video
            cmd_concat = [
                "ffmpeg",
                "-y",
                "-i",
                str(trimmed),
                "-i",
                str(image_clip),
                "-i",
                str(base_video),
                "-filter_complex",
                "[0:v][1:v]concat=n=2:v=1:a=0[outv]",
                "-map",
                "[outv]",
                "-map",
                "2:a",
                "-c:v",
                "libvpx",
                "-cpu-used",
                "5",
                "-crf",
                "40",
                "-b:v",
                "0",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "libopus",
                "-b:a",
                "64k",
                str(output_path),
            ]
            subprocess.run(cmd_concat, check=True)
        finally:
            # Cleanup temporary files
            try:
                shutil.rmtree(tmpdir)
            except Exception:
                pass

    loop = asyncio.get_running_loop()

    await PROCESS_SEMAPHORE.acquire()
    try:
        await loop.run_in_executor(None, process_work)
    finally:
        PROCESS_SEMAPHORE.release()

    await ctx.message.delete()
    await ctx.send(file=discord.File(output_path))

    for file in [image_path, processed_image_path, output_path]:
        with contextlib.suppress(FileNotFoundError):
            file.unlink()


@commands.command(name="wheelhamut")
async def wheelhamut(ctx: commands.Context[commands.Bot]) -> None:

    output_path = "wheelhamut_result.mp4"
    pin_path = "bots/resources/wheelhamut/wheelhamut.png"
    video_size = 360  # Width and height of the output video (square)
    wheel_radius = int(video_size // 2.5)  # Radius of the wheel in pixels
    video_fps = 15  # Frames per second
    spin_seconds = 5  # Total duration of the spin animation
    font_size = video_size // 14  # Font size for segment labels
    pin_size = video_size // 8  # Pin image will be scaled to this size (square)
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

    def render_wheel(ctx: commands.Context[commands.Bot]) -> None:

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

        n = len(names)
        slice_deg = 360.0 / n
        total_frames = video_fps * spin_seconds
        size = video_size

        winner_index = random.randint(0, n - 1)  # noqa: S311
        winner_index = winner_index % n

        pin_angle = 270.0
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
            "libx264",
            "-preset",
            "ultrafast",
            "-tune",
            "zerolatency",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            output_path,
        ]
        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

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
            pin_y = int(video_size // 1.21)  # top edge; adjust if your pin image has its point at the bottom
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

        proc.stdin.close()
        proc.wait()

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, partial(render_wheel, ctx))

    await ctx.send(file=discord.File(output_path))

    with contextlib.suppress(FileNotFoundError):
        Path(output_path).unlink()  # noqa: ASYNC240
