import asyncio
import io
import math
import random
import subprocess
import threading
from pathlib import Path
from typing import BinaryIO

import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont


class CommandWheelhamut(commands.Cog):
    PIN_PATH = Path("project/bots/bahamut/resources/wheelhamut.png")
    FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    VIDEO_SIZE = 360  # Width and height of the output video (square)
    WHEEL_RADIUS = int(VIDEO_SIZE // 2.5)
    VIDEO_FPS = 15
    SPIN_SECONDS = 5
    FONT_SIZE = VIDEO_SIZE // 14
    PIN_SIZE = VIDEO_SIZE // 8
    SCALE = 2
    PAD = 12 * SCALE

    PALETTE = (
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
    )

    _pin_img: Image.Image
    _font_hires: ImageFont.FreeTypeFont | ImageFont.ImageFont

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._process_semaphore = asyncio.Semaphore(1)
        # Static assets loaded once at cog construction — the pin image
        # and font never change, so there's no need to hit disk or
        # re-parse the font file on every command call.
        self._pin_img, self._font_hires = self._load_assets_sync(self.PIN_PATH, self.PIN_SIZE, self.FONT_SIZE, self.SCALE, self.FONT_PATH)

    @staticmethod
    def _load_assets_sync(
        pin_path: Path,
        pin_size: int,
        font_size: int,
        scale: int,
        font_path: str,
    ) -> tuple[Image.Image, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
        pin = Image.open(pin_path).convert("RGBA")
        pin = pin.resize((pin_size, pin_size), Image.Resampling.LANCZOS)

        try:
            font_hires = ImageFont.truetype(font_path, font_size * scale)
        except OSError:
            font_hires = ImageFont.load_default()

        return pin, font_hires

    @classmethod
    def _draw_wheel(
        cls,
        names: list[str],
        angle_offset: float,
        size: int,
        radius: int,
        font_hires: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    ) -> Image.Image:
        """Return a PIL RGBA image of the wheel rotated by angle_offset (degrees)."""
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cx, cy = size // 2, size // 2
        n = len(names)
        slice_deg = 360.0 / n

        for i, name in enumerate(names):
            start_angle = angle_offset + i * slice_deg
            end_angle = start_angle + slice_deg
            color = cls.PALETTE[i % len(cls.PALETTE)]

            bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
            draw.pieslice(bbox, start=start_angle, end=end_angle, fill=color, outline="white")

            mid_angle_rad = math.radians(start_angle + slice_deg / 2)
            tx = cx + radius * 0.65 * math.cos(mid_angle_rad)
            ty = cy + radius * 0.65 * math.sin(mid_angle_rad)

            text_rotation = (start_angle + slice_deg / 2) % 360
            if 90 < text_rotation < 270:  # noqa: PLR2004
                text_rotation += 180

            bbox_hires = font_hires.getbbox(name)
            canvas_w = int((bbox_hires[2] - bbox_hires[0]) + cls.PAD * 2)
            canvas_h = int((bbox_hires[3] - bbox_hires[1]) + cls.PAD * 2)
            txt_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
            txt_draw = ImageDraw.Draw(txt_img)
            txt_draw.text(
                (cls.PAD - bbox_hires[0], cls.PAD - bbox_hires[1]),
                name,
                font=font_hires,
                fill="white",
            )
            txt_img = txt_img.rotate(-text_rotation, expand=True, resample=Image.Resampling.BICUBIC)
            txt_img = txt_img.resize(
                (txt_img.width // cls.SCALE, txt_img.height // cls.SCALE),
                Image.Resampling.LANCZOS,
            )

            paste_x = int(tx - txt_img.width / 2)
            paste_y = int(ty - txt_img.height / 2)
            img.paste(txt_img, (paste_x, paste_y), txt_img)

        draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline="white", width=4)
        hub_r = 18
        draw.ellipse([cx - hub_r, cy - hub_r, cx + hub_r, cy + hub_r], fill="white", outline="#cccccc", width=2)

        return img

    @staticmethod
    def _ease_out_cubic(t: float) -> float:
        """Ease-out cubic: starts fast, decelerates to a stop."""
        return 1 - (1 - t) ** 3

    @classmethod
    def _render_wheel(
        cls,
        names: list[str],
        pin_img: Image.Image,
        font_hires: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    ) -> bytes:
        """Fully synchronous, disk-free render. Runs in an executor thread."""
        size = cls.VIDEO_SIZE
        radius = cls.WHEEL_RADIUS
        n = len(names)
        slice_deg = 360.0 / n
        total_frames = cls.VIDEO_FPS * cls.SPIN_SECONDS

        winner_index = random.randint(0, n - 1)  # noqa: S311
        pin_angle = 90.0
        winning_centre_at_zero = winner_index * slice_deg + slice_deg / 2
        extra_spins = random.randint(5, 8) * 360  # noqa: S311

        start_offset = 0.0
        total_rotation = extra_spins + (pin_angle - winning_centre_at_zero - start_offset) % 360

        # Build the static wheel artwork once so each frame only rotates it.
        wheel_base = cls._draw_wheel(names, 0.0, size, radius, font_hires)

        bg_color = (30, 30, 30)
        pin_size = cls.PIN_SIZE

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
            "rgb24",
            "-r",
            str(cls.VIDEO_FPS),
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
            "frag_keyframe+empty_moov+default_base_moof",
            "-f",
            "mp4",
            "pipe:1",
        ]
        proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Drain stdout/stderr on background threads *while* we write stdin
        # progressively below — without this, ffmpeg's stdout pipe buffer
        # can fill up and deadlock against our still-in-progress stdin writes.
        stdout_chunks: list[bytes] = []
        stderr_chunks: list[bytes] = []

        def drain(pipe: BinaryIO, sink: list[bytes]) -> None:
            sink.extend(iter(lambda: pipe.read(65536), b""))

        stdout_thread = threading.Thread(target=drain, args=(proc.stdout, stdout_chunks))
        stderr_thread = threading.Thread(target=drain, args=(proc.stderr, stderr_chunks))
        stdout_thread.start()
        stderr_thread.start()

        frame_rgb = None
        if proc.stdin is not None:
            try:
                for frame_idx in range(total_frames):
                    t = frame_idx / (total_frames - 1)  # 0.0 -> 1.0
                    eased = cls._ease_out_cubic(t)
                    current_rotation = eased * total_rotation

                    wheel = wheel_base.rotate(-current_rotation, resample=Image.Resampling.BICUBIC)

                    bg = Image.new("RGBA", (size, size), (*bg_color, 255))
                    bg.paste(wheel, (0, 0), wheel)

                    pin_x = size // 2 - pin_size // 2
                    pin_y = int(cls.VIDEO_SIZE // 1.21)
                    bg.paste(pin_img, (pin_x, pin_y), pin_img)

                    frame_rgb = bg.convert("RGB").tobytes()
                    proc.stdin.write(frame_rgb)

                hold_frames = cls.VIDEO_FPS * 2
                if frame_rgb is not None:
                    for _ in range(hold_frames):
                        proc.stdin.write(frame_rgb)
            except BrokenPipeError:
                # ffmpeg exited early — fall through so we still join the reader
                # threads and can report its stderr instead of a bare EPIPE.
                pass
            finally:
                proc.stdin.close()

            proc.wait()
            stdout_thread.join()
            stderr_thread.join()

        if proc.returncode != 0:
            stderr_data = b"".join(stderr_chunks)
            msg = f"ffmpeg failed ({proc.returncode}): {stderr_data.decode(errors='replace')}"
            raise RuntimeError(msg)

        return b"".join(stdout_chunks)

    @commands.command(name="wheelhamut", help="spin da wheel")
    async def wheelhamut(self, ctx: commands.Context[commands.Bot]) -> None:
        message_text = ctx.message.content.removeprefix("!wheelhamut")
        names = [name.strip() for name in message_text.split("\n") if name.strip()] if "\n" in message_text else [name.strip() for name in message_text.split(",") if name.strip()]

        if len(names) < 2:  # noqa: PLR2004
            await ctx.send("give me at least 2 names, comma- or newline-separated")
            return

        loop = asyncio.get_running_loop()
        async with self._process_semaphore:
            output_bytes = await loop.run_in_executor(
                None,
                self._render_wheel,
                names,
                self._pin_img,
                self._font_hires,
            )

        await ctx.send(file=discord.File(io.BytesIO(output_bytes), filename="wheelhamut_result.mp4"))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CommandWheelhamut(bot))
