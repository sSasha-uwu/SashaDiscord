import json
from pathlib import Path

from discord.ext import commands


def get_titan_key() -> str:
    if not ENV_FILE.exists():
        ENV_FILE.write_text("TITAN_API_KEY=your_titan_api_key\nBAHAMUT_API_KEY=your_bahamut_api_key\n", encoding="utf-8")
    return ENV_FILE.read_text(encoding="utf-8").split("TITAN_API_KEY=")[1].splitlines()[0]


def get_bahamut_key() -> str:
    if not ENV_FILE.exists():
        ENV_FILE.write_text("TITAN_API_KEY=your_titan_api_key\nBAHAMUT_API_KEY=your_bahamut_api_key\n", encoding="utf-8")
    return ENV_FILE.read_text(encoding="utf-8").split("BAHAMUT_API_KEY=")[1].splitlines()[0]


EMOTE_LOG = Path("bots/emote_log.json")

ENV_FILE = Path(".env")

BAHAMUT_ERROR_MESSAGE = """
{explode} i hav braim bramage {explode}

pls send help

```{error}```
"""

TITAN_ERROR_MESSAGE = """
{cri} i die now thank u foreva {cri}

my mother is an idiota

```{error}```
"""

TITAN_API_KEY = get_titan_key()
BAHAMUT_API_KEY = get_bahamut_key()

hamut_emotes: dict[str, str] = {}
titan_emotes: dict[str, str] = {}

def get_hamut_emotes(ctx: commands.Context[commands.Bot]) -> dict[str, str]:
    if not hamut_emotes:
        for guild in ctx.bot.guilds:
            for emoji in guild.emojis:
                emoji_raw = str(emoji)
                if "hamut" in emoji_raw:
                    emoji_str = emoji_raw.split(":")[1].split(":", maxsplit=1)[0]
                    hamut_emotes[emoji_str] = emoji_raw
                    print(f"Loaded Bahamut emote: {emoji_str}")
    return hamut_emotes

def get_titan_emotes(ctx: commands.Context[commands.Bot]) -> dict[str, str]:
    if not titan_emotes:
        for guild in ctx.bot.guilds:
            for emoji in guild.emojis:
                emoji_raw = str(emoji)
                if "tan" in emoji_raw:
                    emoji_str = emoji_raw.split(":")[1].split(":", maxsplit=1)[0]
                    titan_emotes[emoji_str] = emoji_raw
                    print(f"Loaded Titan emote: {emoji_str}")
    return titan_emotes


def get_emote_log(bot: str) -> dict[str, int]:
    with EMOTE_LOG.open(mode="r", encoding="utf-8") as f:
        return json.load(f)[bot]  # pyright: ignore[reportAny]


def update_emote_log(emote: str, bot: str) -> None:
    with EMOTE_LOG.open(mode="r", encoding="utf-8") as f:
        emote_log: dict[str, dict[str, int]] = json.load(f)
    if emote not in emote_log[bot]:
        emote_log[bot][emote] = 1
    else:
        emote_log[bot][emote] += 1

    with EMOTE_LOG.open(mode="w", encoding="utf-8") as f:
        json.dump(emote_log, f, indent=4)
