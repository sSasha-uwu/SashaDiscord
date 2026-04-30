import asyncio
import json
import multiprocessing
from collections.abc import Callable

from common import EMOTE_LOG, ENV_FILE

from bots.bahamut import bahamut_bot
from bots.titan import titan_bot


def run_titan_bot() -> None:
    asyncio.run(titan_bot())


def run_bahamut_bot() -> None:
    asyncio.run(bahamut_bot())


bots: dict[str, Callable[[], None]] = {
    "Titan": run_titan_bot,
    "Bahamut": run_bahamut_bot,
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
