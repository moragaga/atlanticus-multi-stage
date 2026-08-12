# El provider local es determinista y no recibe datos de usuario por variables.
from __future__ import annotations

from flask import Request

from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.identity.provider import IdentityProvider


class LocalIdentityProvider(IdentityProvider):
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
            subject_id='local:john-doe',
        )
