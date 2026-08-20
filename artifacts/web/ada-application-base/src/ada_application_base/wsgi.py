from __future__ import annotations

import atexit
from collections.abc import Callable
from threading import Lock
from typing import Any

from ada_application_base.application import AdaApplicationBaseRuntime, create_application_runtime

RuntimeFactory = Callable[[], AdaApplicationBaseRuntime]


class WorkerApplication:
    def __init__(self, factory: RuntimeFactory = create_application_runtime) -> None:
        self._factory = factory
        self._lock = Lock()
        self._runtime: AdaApplicationBaseRuntime | None = None
        self._exit_registered = False

    def warmup(self) -> None:
        if self._runtime is not None:
            return
        with self._lock:
            if self._runtime is not None:
                return
            self._runtime = self._factory()
            if not self._exit_registered:
                atexit.register(self.close)
                self._exit_registered = True

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]):
        runtime = self._runtime
        if runtime is None:
            raise RuntimeError('ADA Application Base worker runtime is not initialized')
        return runtime.server(environ, start_response)

    def close(self) -> None:
        with self._lock:
            runtime = self._runtime
            self._runtime = None
        if runtime is not None:
            runtime.close()


app = WorkerApplication()
