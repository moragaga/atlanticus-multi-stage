from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock


class Gate:
    """Non-blocking single-flight gate.

    A caller either enters immediately or skips the protected operation. It never waits
    behind another slow execution, which prevents callback and refresh queues from growing.
    """

    def __init__(self) -> None:
        self._lock = Lock()

    @contextmanager
    def enter(self) -> Iterator[bool]:
        entered = self._lock.acquire(blocking=False)
        try:
            yield entered
        finally:
            if entered:
                self._lock.release()

    @property
    def busy(self) -> bool:
        return self._lock.locked()
