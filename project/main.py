import json
import multiprocessing
from collections.abc import Callable

from common import EMOTE_LOG, ENV_FILE

from bots.bahamut import bahamut_bot
from bots.titan import titan_bot

processes: list[multiprocessing.Process] = []
bots: list[Callable[..., None]] = [
    titan_bot,
    bahamut_bot,
]


def run_bots() -> None:
    for process in processes:
        process.terminate()
        process.join()  # ← Wait for the process to fully stop
    processes.clear()
    for bot_function in bots:
        process = multiprocessing.Process(target=bot_function)
        process.start()
        processes.append(process)


if __name__ == "__main__":
    if not EMOTE_LOG.exists():
        with EMOTE_LOG.open(mode="w", encoding="utf-8") as f:
            json.dump({"titan": {}, "bahamut": {}}, f, indent=4)
    if not ENV_FILE.exists():
        with ENV_FILE.open(mode="w", encoding="utf-8") as f:
            f.write(
                "TITAN_API_KEY=your_titan_api_key\n"
                "BAHAMUT_API_KEY=your_bahamut_api_key\n",
            )
    run_bots()
