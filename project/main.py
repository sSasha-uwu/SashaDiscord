import json
import math
import multiprocessing
import random
import sys
from collections.abc import Callable

import cv2
import numpy as np
from common import EMOTE_LOG, ENV_FILE
from PIL import Image, ImageDraw, ImageFont

from bots.bahamut import bahamut_bot
from bots.titan import titan_bot

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

VIDEO_SIZE = 800  # Width and height of the output video (square)
WHEEL_RADIUS = 320  # Radius of the wheel in pixels
FPS = 24  # Frames per second
SPIN_SECONDS = 5  # Total duration of the spin animation
FONT_SIZE = 56  # Font size for segment labels
PIN_SIZE = 100  # Pin image will be scaled to this size (square)
SCALE = 2
PAD = 12 * SCALE

# Palette — segments cycle through these colours
PALETTE = [
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


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------


def draw_wheel(names: list[str], angle_offset: float, size: int, radius: int) -> Image.Image:
    """Return a PIL RGBA image of the wheel rotated by angle_offset (degrees)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    n = len(names)
    slice_deg = 360.0 / n

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SIZE)
        font_hires = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SIZE * SCALE)
    except OSError:
        font = ImageFont.load_default(FONT_SIZE)
        font_hires = font

    for i, name in enumerate(names):
        start_angle = angle_offset + i * slice_deg
        end_angle = start_angle + slice_deg
        color = PALETTE[i % len(PALETTE)]

        bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
        draw.pieslice(bbox, start=start_angle, end=end_angle, fill=color, outline="white")

        mid_angle_rad = math.radians(start_angle + slice_deg / 2)
        tx = cx + radius * 0.65 * math.cos(mid_angle_rad)
        ty = cy + radius * 0.65 * math.sin(mid_angle_rad)

        text_rotation = (start_angle + slice_deg / 2) % 360

        if 90 < text_rotation < 270:  # noqa: PLR2004
            text_rotation += 180

        bbox_hires = font_hires.getbbox(name)
        canvas_w = (bbox_hires[2] - bbox_hires[0]) + PAD * 2
        canvas_h = (bbox_hires[3] - bbox_hires[1]) + PAD * 2
        txt_img = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
        txt_draw = ImageDraw.Draw(txt_img)
        txt_draw.text(
            (PAD - bbox_hires[0], PAD - bbox_hires[1]),
            name,
            font=font_hires,
            fill="white",
        )
        txt_img = txt_img.rotate(-text_rotation, expand=True, resample=Image.Resampling.BICUBIC)
        txt_img = txt_img.resize(
            (txt_img.width // SCALE, txt_img.height // SCALE),
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


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------


def generate_spin_video(
    names: list[str],
    pin_path: str,
    output_path: str = "spin_result.mp4",
    winner_index: int | None = None,
) -> str:
    if not names:
        raise ValueError("names list must not be empty.")

    n = len(names)
    slice_deg = 360.0 / n
    total_frames = FPS * SPIN_SECONDS
    size = VIDEO_SIZE

    # Choose winner
    if winner_index is None:
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
    pin_img = load_pin(pin_path, PIN_SIZE)

    # Composite background colour
    bg_color = (30, 30, 30)

    # Set up video writer
    fourcc = cv2.VideoWriter.fourcc(*"vp80")
    writer = cv2.VideoWriter(output_path, fourcc, FPS, (size, size))

    print(f"Rendering {total_frames} frames → winner: '{winner_name}' (index {winner_index})")

    for frame_idx in range(total_frames):
        t = frame_idx / (total_frames - 1)  # 0.0 → 1.0
        eased = ease_out_cubic(t)
        current_rotation = eased * total_rotation  # degrees rotated so far

        angle_offset = start_offset - current_rotation  # subtract = clockwise spin

        # Draw wheel
        wheel = draw_wheel(names, angle_offset, size, WHEEL_RADIUS)

        # Composite onto background
        bg = Image.new("RGBA", (size, size), (*bg_color, 255))
        bg.paste(wheel, (0, 0), wheel)

        # Paste pin at top-centre
        pin_x = size // 2 - PIN_SIZE // 2
        pin_y = 660  # top edge; adjust if your pin image has its point at the bottom
        bg.paste(pin_img, (pin_x, pin_y), pin_img)

        # Convert to BGR for OpenCV
        frame_np = np.array(bg.convert("RGB"))
        frame_bgr = cv2.cvtColor(frame_np, cv2.COLOR_RGB2BGR)
        writer.write(frame_bgr)

        if frame_idx % FPS == 0:
            print(f"  Frame {frame_idx}/{total_frames} ({int(t * 100)}%)")

    # Hold final frame for 2 seconds
    hold_frames = FPS * 2

    for _ in range(hold_frames):
        writer.write(frame_bgr)

    writer.release()
    print(f"\nDone! Video saved to: {output_path}")
    print(f"Winner: {winner_name}")
    return output_path


# ---------------------------------------------------------------------------
# Example / quick test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample_names = [
        "Alice",
        "Bob",
        "Carol",
        "Dave",
        "Eve",
        "Frank",
        "Grace",
        "Heidi",
    ]

    # Replace with your actual pin image path
    PIN_IMAGE_PATH = "bots/resources/wheelhamut/wheelhamut.png"

    generate_spin_video(
        names=sample_names,
        pin_path=PIN_IMAGE_PATH,
        output_path="spin_result.webm",
        winner_index=None,
    )

sys.exit()

bots: dict[str, Callable[[], None]] = {
    "Titan": titan_bot,
    "Bahamut": bahamut_bot,
}


if __name__ == "__main__":
    if not EMOTE_LOG.exists():
        with EMOTE_LOG.open(mode="w", encoding="utf-8") as f:
            json.dump({"titan": {}, "bahamut": {}}, f, indent=4)
    if not ENV_FILE.exists():
        with ENV_FILE.open(mode="w", encoding="utf-8") as f:
            titan_api_key = input("Enter your Titan API key: ")
            bahamut_api_key = input("Enter your Bahamut API key: ")
            f.write(
                f"TITAN_API_KEY={titan_api_key}\nBAHAMUT_API_KEY={bahamut_api_key}\n",
            )
    for bot_name, bot_function in bots.items():
        new_process = multiprocessing.Process(target=bot_function)
        new_process.start()
        print(f"{bot_name} bot started with PID: {new_process.pid}")
