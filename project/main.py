import json

from project.bots.bahamut.bot import BahamutBot
from project.common import EMOTE_LOG

if __name__ == "__main__":
    if not EMOTE_LOG.exists():
        with EMOTE_LOG.open(mode="w", encoding="utf-8") as f:
            json.dump({"titan": {}, "bahamut": {}}, f, indent=4)
    BahamutBot()
