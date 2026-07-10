import asyncio
import io
import json
import os
import subprocess
import threading
from pathlib import Path

import discord
from discord.ext import commands
from PIL import Image


class CommandLayhamut(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._process_semaphore = asyncio.Semaphore(1)
        self._base_video_bytes, self._base_video_info = self._load_base_video_sync(Path("project/bots/bahamut/resources/layhamut.webm"))

    @commands.command(name="layhamut", help="have bahamut execute someone")
    async def layhamut(self, ctx: commands.Context[commands.Bot]) -> None:
        if not ctx.message.attachments:
            await ctx.send("where image")
            return

        image_bytes = await ctx.message.attachments[0].read()

        loop = asyncio.get_running_loop()
        async with self._process_semaphore:
            output_bytes = await loop.run_in_executor(
                None,
                self._render_layhamut,
                image_bytes,
                self._base_video_bytes,
                self._base_video_info,
            )

        await ctx.message.delete()
        await ctx.send(file=discord.File(io.BytesIO(output_bytes), filename="layhamut.webm"))

    @staticmethod
    def _load_base_video_sync(path: Path) -> tuple[bytes, tuple[int, int, float, float]]:
        video_bytes = path.read_bytes()

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
        width, height = int(stream["width"]), int(stream["height"])
        num, den = map(int, stream.get("r_frame_rate", "25/1").split("/"))
        fps = num / den if den else 25.0
        duration = float(data.get("format", {}).get("duration", 0.0))

        return video_bytes, (width, height, fps, duration)

    @staticmethod
    def _render_layhamut(
        image_bytes: bytes,
        base_video_bytes: bytes,
        base_video_info: tuple[int, int, float, float],
    ) -> bytes:
        """Fully synchronous, disk-free render. Runs in an executor thread."""
        src_w, src_h, src_fps, src_dur = base_video_info

        target_fps = min(round(src_fps), 15)
        max_width = 480
        if src_w > max_width:
            target_w = max_width
            target_h = int(src_h * (max_width / src_w))
        else:
            target_w, target_h = src_w, src_h

        img_dur = 12 / src_fps
        final_duration = max(0.5, src_dur - img_dur)

        with Image.open(io.BytesIO(image_bytes)) as img:
            img_aspect = img.width / img.height
            frame_aspect = target_w / target_h

            if img_aspect > frame_aspect:
                new_w = target_w
                new_h = int(target_w / img_aspect)
                resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", (target_w, target_h), (0, 0, 0))
                canvas.paste(resized, (0, (target_h - new_h) // 2))
            else:
                new_h = target_h
                new_w = int(target_h * img_aspect)
                resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", (target_w, target_h), (0, 0, 0))
                canvas.paste(resized, ((target_w - new_w) // 2, 0))

            frame_bytes = canvas.convert("RGB").tobytes()

        frames_count = max(1, round(img_dur * target_fps))
        stdin_payload = frame_bytes * frames_count

        filter_complex = (
            f"[0:v]trim=0:{final_duration},setpts=PTS-STARTPTS,scale={target_w}:{target_h}[v0];"
            f"[1:v]format=rgb24,format=yuv420p,setsar=1,trim=duration={img_dur},setpts=PTS-STARTPTS[v1];"
            f"[v0][v1]concat=n=2:v=1:a=0[outv]"
        )

        base_read_fd, base_write_fd = os.pipe()

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            f"pipe:{base_read_fd}",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            f"{target_w}x{target_h}",
            "-r",
            str(target_fps),
            "-i",
            "-",
            "-filter_complex",
            filter_complex,
            "-map",
            "[outv]",
            "-map",
            "0:a",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-tune",
            "zerolatency",
            "-crf",
            "30",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "libopus",
            "-b:a",
            "64k",
            "-movflags",
            "frag_keyframe+empty_moov+default_base_moof",
            "-f",
            "mp4",
            "pipe:1",
        ]

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            pass_fds=(base_read_fd,),
        )
        os.close(base_read_fd)

        def feed_base_video() -> None:
            with os.fdopen(base_write_fd, "wb") as f:
                f.write(base_video_bytes)

        writer = threading.Thread(target=feed_base_video)
        writer.start()
        try:
            stdout_data, stderr_data = proc.communicate(input=stdin_payload)
        finally:
            writer.join()

        if proc.returncode != 0:
            msg = f"ffmpeg failed ({proc.returncode}): {stderr_data.decode(errors='replace')}"
            raise RuntimeError(msg)

        return stdout_data


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CommandLayhamut(bot))
