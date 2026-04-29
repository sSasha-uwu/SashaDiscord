import json
import multiprocessing
import time
from collections.abc import Callable
from typing import override

from common import EMOTE_LOG, ENV_FILE
from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from bots.bahamut import bahamut_bot
from bots.titan import titan_bot

processes: list[multiprocessing.Process] = []
bots: list[Callable[..., None]] = [
    titan_bot,
    bahamut_bot,
]


class ReloadHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        self._last_reload = 0.0
        self._cooldown = 2.0  # seconds

    @override
    def on_modified(self, event: FileSystemEvent) -> None:
        now = time.time()
        if (
            str(event.src_path).endswith(".py")
            and ".venv" not in str(event.src_path)
            and now - self._last_reload > self._cooldown
        ):
            self._last_reload = now
            run_bots()
            print("=============================================================")
            print(f"Reloaded bots due to changes in {event.src_path}")
            print("=============================================================")


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
    event_handler = ReloadHandler()
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()
    run_bots()
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
