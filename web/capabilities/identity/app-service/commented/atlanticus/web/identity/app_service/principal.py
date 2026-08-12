# Este módulo interpreta únicamente el principal inyectado por App Service Easy Auth.
# No decodifica ni consume access tokens o id tokens del proveedor subyacente.
# Los claims se normalizan a datos mínimos para el contrato neutral de Identity.

from __future__ import annotations

import base64
import json
from collections.abc import Mapping
from dataclasses import dataclass

from atlanticus.web.identity.errors import IdentityAuthenticationError

CLIENT_PRINCIPAL_HEADER = 'X-MS-CLIENT-PRINCIPAL'
CLIENT_PRINCIPAL_ID_HEADER = 'X-MS-CLIENT-PRINCIPAL-ID'
CLIENT_PRINCIPAL_NAME_HEADER = 'X-MS-CLIENT-PRINCIPAL-NAME'
CLIENT_PRINCIPAL_IDP_HEADER = 'X-MS-CLIENT-PRINCIPAL-IDP'

_AAD_PROVIDER_KEY = 'aad'
_OID_CLAIMS = (
    'http://schemas.microsoft.com/identity/claims/objectidentifier',
    'oid',
)
_TENANT_CLAIMS = (
    'http://schemas.microsoft.com/identity/claims/tenantid',
    'tid',
)
_EMAIL_CLAIMS = (
    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress',
    'email',
    'preferred_username',
    'upn',
)
_NAME_CLAIMS = ('name',)
_ISSUER_CLAIMS = ('iss',)
_SUBJECT_CLAIMS = (
    'sub',
    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier',
)


@dataclass(frozen=True, slots=True)
class AppServicePrincipal:
    identity_provider: str
    claims: Mapping[str, tuple[str, ...]]

    def claim(self, *names: str) -> str | None:
        for name in names:
            values = self.claims.get(name)
            if values:
                if any(value != values[0] for value in values[1:]):
                    raise IdentityAuthenticationError(
                        f'App Service principal has conflicting values for claim {name!r}'
                    )
                return values[0]
        return None


def decode_client_principal(value: str) -> AppServicePrincipal:
    encoded = value.strip()
    if not encoded:
        raise IdentityAuthenticationError('App Service client principal header is empty')

    try:
        padding = '=' * (-len(encoded) % 4)
        decoded = base64.b64decode(
            f'{encoded}{padding}',
            altchars=b'-_',
            validate=True,
        )
        payload = json.loads(decoded.decode('utf-8'))
    except ValueError as error:
        raise IdentityAuthenticationError('App Service client principal is invalid') from error

    if not isinstance(payload, dict):
        raise IdentityAuthenticationError('App Service client principal must be a JSON object')

    identity_provider = _required_string(payload.get('auth_typ'), 'identity provider')
    claims_value = payload.get('claims')
    if not isinstance(claims_value, list):
        raise IdentityAuthenticationError('App Service client principal claims must be a list')

    claims: dict[str, list[str]] = {}
    for item in claims_value:
        if not isinstance(item, dict):
            raise IdentityAuthenticationError('App Service client principal claim is invalid')
        claim_type = _required_string(item.get('typ'), 'claim type')
        claim_value = _required_string(item.get('val'), 'claim value')
        claims.setdefault(claim_type, []).append(claim_value)

    return AppServicePrincipal(
        identity_provider=identity_provider.casefold(),
        claims={key: tuple(values) for key, values in claims.items()},
    )


def resolve_subject_id(
    principal: AppServicePrincipal,
    headers: Mapping[str, str],
) -> str:
    header_subject = _optional_string(headers.get(CLIENT_PRINCIPAL_ID_HEADER))
    if principal.identity_provider == _AAD_PROVIDER_KEY:
        claim_subject = principal.claim(*_OID_CLAIMS)
        if claim_subject and header_subject and claim_subject != header_subject:
            raise IdentityAuthenticationError('App Service principal identifiers do not match')
        subject_id = claim_subject or header_subject
        if subject_id is None:
            raise IdentityAuthenticationError(
                'App Service AAD principal is missing object identifier'
            )
        return subject_id

    subject_id = header_subject or principal.claim(*_SUBJECT_CLAIMS)
    if subject_id is None:
        raise IdentityAuthenticationError('App Service principal is missing subject identifier')
    return subject_id


def resolve_issuer(principal: AppServicePrincipal) -> str:
    issuer = principal.claim(*_ISSUER_CLAIMS)
    if issuer is not None:
        return issuer

    if principal.identity_provider == _AAD_PROVIDER_KEY:
        tenant_id = principal.claim(*_TENANT_CLAIMS)
        if tenant_id is None:
            raise IdentityAuthenticationError(
                'App Service AAD principal is missing issuer or tenant'
            )
        return f'app_service:aad:tenant:{tenant_id}'

    return f'app_service:{principal.identity_provider}'


def resolve_display_name(principal: AppServicePrincipal) -> str | None:
    return principal.claim(*_NAME_CLAIMS)


def resolve_email(
    principal: AppServicePrincipal,
    headers: Mapping[str, str],
) -> str | None:
    email = principal.claim(*_EMAIL_CLAIMS)
    if email is not None:
        return email

    principal_name = _optional_string(headers.get(CLIENT_PRINCIPAL_NAME_HEADER))
    if principal_name is not None and '@' in principal_name:
        return principal_name
    return None


def validate_identity_provider_header(
    principal: AppServicePrincipal,
    headers: Mapping[str, str],
) -> None:
    header_provider = _optional_string(headers.get(CLIENT_PRINCIPAL_IDP_HEADER))
    if header_provider is None:
        return
    if header_provider.casefold() != principal.identity_provider:
        raise IdentityAuthenticationError('App Service identity provider headers do not match')


def _required_string(value: object, label: str) -> str:
    normalized = _optional_string(value)
    if normalized is None:
        raise IdentityAuthenticationError(f'App Service {label} is missing')
    return normalized


def _optional_string(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None
