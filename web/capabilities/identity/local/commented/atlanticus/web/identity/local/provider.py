# Selecciona una identidad local al crear el provider y la mantiene estable durante esa ejecución.
from __future__ import annotations

import secrets

from flask import Request

from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.identity.provider import IdentityProvider

_LOCAL_SUBJECT_IDS = ('local:john-doe', 'local:jane-doe')


class LocalIdentityProvider(IdentityProvider):
    def __init__(self) -> None:
        self._subject_id = secrets.choice(_LOCAL_SUBJECT_IDS)

    @property
    def key(self) -> str:
        return 'local'

    @property
    def production_ready(self) -> bool:
        return False

    def validate_configuration(self) -> None:
        return None

    def resolve(self, request: Request) -> AuthenticatedIdentity:
        del request
        return AuthenticatedIdentity(
            provider_key='local',
            issuer='atlanticus-local',
            subject_id=self._subject_id,
        )
