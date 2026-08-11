# El bootstrap limpia el snapshot previo y ejecuta provider + resolver solo al refrescar la página.
from __future__ import annotations

from flask import Request

from atlanticus.web.identity.access import (
    AccessResolver,
    AccessRuntime,
    AccessSnapshot,
)
from atlanticus.web.identity.errors import IdentityAuthenticationError
from atlanticus.web.identity.provider import IdentityProvider


class AccessBootstrap:
    def __init__(
        self,
        *,
        provider: IdentityProvider,
        resolver: AccessResolver,
        runtime: AccessRuntime,
    ) -> None:
        self._provider = provider
        self._resolver = resolver
        self._runtime = runtime

    def refresh(self, request: Request) -> AccessSnapshot:
        try:
            self._runtime.clear()
            identity = self._provider.resolve(request)
        except IdentityAuthenticationError:
            snapshot = AccessSnapshot.invalid_identity()
            self._runtime.store(snapshot)
            return snapshot

        decision = self._resolver.resolve(identity)
        snapshot = AccessSnapshot.resolved(identity=identity, decision=decision)
        self._runtime.store(snapshot)
        return snapshot
