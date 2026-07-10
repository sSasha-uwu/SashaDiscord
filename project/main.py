import json
from multiprocessing import Process

from project.bots.bahamut.bot import BahamutBot
from project.bots.titan.bot import TitanBot
from project.common import EMOTE_LOG

if __name__ == "__main__":
    if not EMOTE_LOG.exists():
        with EMOTE_LOG.open(mode="w", encoding="utf-8") as f:
            json.dump({"titan": {}, "bahamut": {}}, f, indent=4)

    bahamut_process = Process(target=BahamutBot)
    titan_process = Process(target=TitanBot)

    bahamut_process.start()
    titan_process.start()

    bahamut_process.join()
    titan_process.join()
