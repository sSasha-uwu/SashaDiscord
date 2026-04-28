import multiprocessing
from collections.abc import Callable
from typing import override

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
    @override
    def on_modified(self, event: FileSystemEvent) -> None:
        if str(event.src_path).endswith(".py") and ".venv" not in str(
            event.src_path,
        ):
            run_bots()


def run_bots() -> None:
    for process in processes:
        process.terminate()
    processes.clear()
    for bot_function in bots:
        process = multiprocessing.Process(target=bot_function)
        process.start()
        processes.append(process)


if __name__ == "__main__":
    event_handler = ReloadHandler()
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()
    run_bots()
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
