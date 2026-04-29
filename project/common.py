#!/usr/bin/env python
# Copyright 2025
"""..."""

import json
from pathlib import Path


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

BOT_ERROR_MESSAGE = """
<a:explodehamut:1016989707973951529> i hav braim bramage <a:explodehamut:1016989707973951529>

pls send help

```{error}```
"""

TITAN_API_KEY = get_titan_key()
BAHAMUT_API_KEY = get_bahamut_key()


def get_emote_log(bot: str) -> dict[str, int]:
    """...

    Returns
    -------
        dict[str, int]: The emote log for the given bot.

    """
    with EMOTE_LOG.open(mode="r", encoding="utf-8") as f:
        return json.load(f)[bot]  # pyright: ignore[reportAny]


def update_emote_log(emote: str, bot: str) -> None:
    """..."""
    with EMOTE_LOG.open(mode="r", encoding="utf-8") as f:
        emote_log: dict[str, dict[str, int]] = json.load(f)
    if emote not in emote_log[bot]:
        emote_log[bot][emote] = 1
    else:
        emote_log[bot][emote] += 1

    with EMOTE_LOG.open(mode="w", encoding="utf-8") as f:
        json.dump(emote_log, f, indent=4)
