from __future__ import annotations

import atexit
from collections.abc import Callable
from threading import Lock
from typing import Any

from ada_application_base.application import AdaApplicationBaseRuntime, create_application_runtime

RuntimeFactory = Callable[[], AdaApplicationBaseRuntime]


class WorkerApplication:
    # El import WSGI solo crea este contenedor liviano; no abre Cosmos ni compone Dash.
    def __init__(self, factory: RuntimeFactory = create_application_runtime) -> None:
        self._factory = factory
        self._lock = Lock()
        self._runtime: AdaApplicationBaseRuntime | None = None
        self._exit_registered = False

    # Gunicorn llama este método después de que el worker fue inicializado y después del fork.
    def warmup(self) -> None:
        if self._runtime is not None:
            return
        with self._lock:
            if self._runtime is not None:
                return
            # Dash, páginas y clientes nacen antes de atender requests y pertenecen al worker.
            self._runtime = self._factory()
            if not self._exit_registered:
                atexit.register(self.close)
                self._exit_registered = True

    def __call__(self, environ: dict[str, Any], start_response: Callable[..., Any]):
        runtime = self._runtime
        if runtime is None:
            # Evita volver a componer Dash dentro de un request WSGI.
            raise RuntimeError('ADA Application Base worker runtime is not initialized')
        return runtime.server(environ, start_response)

    def close(self) -> None:
        with self._lock:
            runtime = self._runtime
            self._runtime = None
        if runtime is not None:
            # El mismo worker que abrió la infraestructura es responsable de cerrarla.
            runtime.close()


# El master puede importar este objeto incluso con preload local sin heredar clientes abiertos.
app = WorkerApplication()
