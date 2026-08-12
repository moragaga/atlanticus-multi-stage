# Provider productivo para Azure App Service Easy Auth.
# Su responsabilidad termina al producir AuthenticatedIdentity desde headers X-MS-*.

from __future__ import annotations

from flask import Request

from atlanticus.web.identity.app_service.principal import (
    CLIENT_PRINCIPAL_HEADER,
    decode_client_principal,
    resolve_display_name,
    resolve_email,
    resolve_issuer,
    resolve_subject_id,
    validate_identity_provider_header,
)
from atlanticus.web.identity.errors import IdentityAuthenticationError
from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.identity.provider import IdentityProvider


class AppServiceIdentityProvider(IdentityProvider):
    @property
    def key(self) -> str:
        return 'app_service'

    @property
    def production_ready(self) -> bool:
        return True

    def validate_configuration(self) -> None:
        return None

    def resolve(self, request: Request) -> AuthenticatedIdentity:
        raw_principal = request.headers.get(CLIENT_PRINCIPAL_HEADER)
        if raw_principal is None:
            raise IdentityAuthenticationError('App Service client principal header is missing')

        principal = decode_client_principal(raw_principal)
        validate_identity_provider_header(principal, request.headers)
        return AuthenticatedIdentity(
            provider_key=self.key,
            issuer=resolve_issuer(principal),
            subject_id=resolve_subject_id(principal, request.headers),
            display_name=resolve_display_name(principal),
            email=resolve_email(principal, request.headers),
        )
