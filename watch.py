import http.server
import os
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from build import build


def foo():
    """Called whenever a change is detected in the watched directory."""
    print("Change detected — running foo()")


class ChangeHandler(FileSystemEventHandler):
    IGNORED_DIRS = {Path("./output").resolve()}

    def _is_ignored(self, path: str) -> bool:
        p = Path(path).resolve()
        return any(
            p == ignored or ignored in p.parents for ignored in self.IGNORED_DIRS
        )

    def on_any_event(self, event):
        if event.is_directory:
            return
        if self._is_ignored(str(event.src_path)):
            return
        print(f"[{event.event_type}] {event.src_path}")
        build()


def start_server(directory="./output", port=8000):
    abs_directory = os.path.abspath(directory)  # ← resolve to absolute path

    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=abs_directory, **kwargs)

    server = http.server.HTTPServer(("", port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"Serving '{directory}' at http://localhost:{port}")
    return server


if __name__ == "__main__":
    build()
    watch_path = "."
    handler = ChangeHandler()
    observer = Observer()
    observer.schedule(handler, path=watch_path, recursive=True)
    observer.start()
    print(f"Watching '{watch_path}' (excluding ./output) — press Ctrl+C to stop")
    start_server()
    print("Starting server on port 8000")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()
