#!/usr/bin/env python
# Copyright 2025
"""..."""

import json
from pathlib import Path

EMOTE_LOG = Path("bots/emote_log.json")

TITAN_DISCORD_ID = 0
TITAN_API_KEY = ""

BAHAMUT_DISCORD_ID = 0
BAHAMUT_API_KEY = ""


BOT_ERROR_MESSAGE = """
<a:explodehamut:1016989707973951529> i hav braim bramage <a:explodehamut:1016989707973951529>

pls send help

```{error}```
"""


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
