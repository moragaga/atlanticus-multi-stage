from __future__ import annotations

import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from ada.compositions.web_bootstrap import ensure_ada_cosmos_infrastructure
from ada_application_base.definition import build_deployment_definition
from atlanticus.web.compositions.runtime_infrastructure import resolve_cosmos_connections
from atlanticus.web.environment import EnvironmentReader

_READY_TIMEOUT_SECONDS = 120.0
_READY_INTERVAL_SECONDS = 1.0


def main() -> None:
    _wait_until_ready()
    environment = EnvironmentReader()
    definition = build_deployment_definition(environment)
    connections = resolve_cosmos_connections(environment, definition.cosmos_connections)
    ensure_ada_cosmos_infrastructure(
        cosmos_connections=connections,
        bindings=definition.bindings,
        create_databases_if_missing=True,
    )
    print(f"ADA Application Base local Cosmos ready: {os.environ['ATLANTICUS_COSMOS_DATABASE']}")


def _wait_until_ready() -> None:
    ready_url = os.environ['ATLANTICUS_COSMOS_READY_URL']
    deadline = time.monotonic() + _READY_TIMEOUT_SECONDS
    last_error: BaseException | None = None
    while time.monotonic() < deadline:
        try:
            with urlopen(ready_url, timeout=2.0) as response:
                if 200 <= response.status < 300:
                    return
        except (HTTPError, URLError, TimeoutError, OSError) as error:
            last_error = error
        time.sleep(_READY_INTERVAL_SECONDS)
    raise RuntimeError('Cosmos emulator did not become ready') from last_error


if __name__ == '__main__':
    main()
