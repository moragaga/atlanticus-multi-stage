import base64
import json
from pathlib import Path

import pytest
from flask import Flask, request

from atlanticus.web.identity.app_service import AppServiceIdentityProvider
from atlanticus.web.identity.errors import IdentityAuthenticationError

_FIXTURE = Path(__file__).parent / 'fixtures' / 'aad_principal.json'
_OID = '11111111-1111-1111-1111-111111111111'
_ISSUER = 'https://login.microsoftonline.com/22222222-2222-2222-2222-222222222222/v2.0'


def _encode(payload: dict[str, object]) -> str:
    return base64.b64encode(json.dumps(payload).encode('utf-8')).decode('ascii')


def _fixture() -> dict[str, object]:
    return json.loads(_FIXTURE.read_text(encoding='utf-8'))


def _resolve(headers: dict[str, str]):
    app = Flask(__name__)
    with app.test_request_context('/', headers=headers):
        return AppServiceIdentityProvider().resolve(request)


def test_aad_principal_maps_real_easy_auth_claim_shape() -> None:
    identity = _resolve(
        {
            'X-MS-CLIENT-PRINCIPAL': _encode(_fixture()),
            'X-MS-CLIENT-PRINCIPAL-ID': _OID,
            'X-MS-CLIENT-PRINCIPAL-NAME': 'john.doe@example.com',
            'X-MS-CLIENT-PRINCIPAL-IDP': 'aad',
        }
    )

    assert identity.provider_key == 'app_service'
    assert identity.subject_id == _OID
    assert identity.issuer == _ISSUER
    assert identity.display_name == 'John Doe'
    assert identity.email == 'john.doe@example.com'


def test_aad_principal_ignores_provider_token_headers() -> None:
    identity = _resolve(
        {
            'X-MS-CLIENT-PRINCIPAL': _encode(_fixture()),
            'X-MS-TOKEN-AAD-ACCESS-TOKEN': 'must-not-be-read',
            'X-MS-TOKEN-AAD-ID-TOKEN': 'must-not-be-read',
        }
    )

    assert identity.subject_id == _OID


def test_missing_principal_header_is_invalid_identity() -> None:
    with pytest.raises(IdentityAuthenticationError, match='header is missing'):
        _resolve({})


def test_invalid_base64_is_invalid_identity() -> None:
    with pytest.raises(IdentityAuthenticationError, match='principal is invalid'):
        _resolve({'X-MS-CLIENT-PRINCIPAL': '%%%invalid%%%'})


def test_invalid_json_is_invalid_identity() -> None:
    value = base64.b64encode(b'not-json').decode('ascii')

    with pytest.raises(IdentityAuthenticationError, match='principal is invalid'):
        _resolve({'X-MS-CLIENT-PRINCIPAL': value})


def test_aad_requires_oid_or_principal_id() -> None:
    payload = _fixture()
    payload['claims'] = [
        claim
        for claim in payload['claims']
        if claim['typ'] != 'http://schemas.microsoft.com/identity/claims/objectidentifier'
    ]

    with pytest.raises(IdentityAuthenticationError, match='object identifier'):
        _resolve({'X-MS-CLIENT-PRINCIPAL': _encode(payload)})


def test_aad_rejects_conflicting_oid_and_principal_id() -> None:
    with pytest.raises(IdentityAuthenticationError, match='identifiers do not match'):
        _resolve(
            {
                'X-MS-CLIENT-PRINCIPAL': _encode(_fixture()),
                'X-MS-CLIENT-PRINCIPAL-ID': '33333333-3333-3333-3333-333333333333',
            }
        )


def test_aad_uses_principal_id_when_oid_claim_is_not_available() -> None:
    payload = _fixture()
    payload['claims'] = [
        claim
        for claim in payload['claims']
        if claim['typ'] != 'http://schemas.microsoft.com/identity/claims/objectidentifier'
    ]

    identity = _resolve(
        {
            'X-MS-CLIENT-PRINCIPAL': _encode(payload),
            'X-MS-CLIENT-PRINCIPAL-ID': _OID,
        }
    )

    assert identity.subject_id == _OID


def test_email_falls_back_to_principal_name() -> None:
    payload = _fixture()
    excluded = {
        'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress',
        'preferred_username',
    }
    payload['claims'] = [claim for claim in payload['claims'] if claim['typ'] not in excluded]

    identity = _resolve(
        {
            'X-MS-CLIENT-PRINCIPAL': _encode(payload),
            'X-MS-CLIENT-PRINCIPAL-NAME': 'fallback@example.com',
        }
    )

    assert identity.email == 'fallback@example.com'


def test_identity_provider_header_must_match_principal() -> None:
    with pytest.raises(IdentityAuthenticationError, match='provider headers do not match'):
        _resolve(
            {
                'X-MS-CLIENT-PRINCIPAL': _encode(_fixture()),
                'X-MS-CLIENT-PRINCIPAL-IDP': 'google',
            }
        )


def test_generic_app_service_provider_uses_documented_principal_id() -> None:
    payload = {
        'auth_typ': 'google',
        'claims': [
            {'typ': 'name', 'val': 'Jane Doe'},
            {'typ': 'email', 'val': 'jane@example.com'},
        ],
    }

    identity = _resolve(
        {
            'X-MS-CLIENT-PRINCIPAL': _encode(payload),
            'X-MS-CLIENT-PRINCIPAL-ID': 'google-user-1',
            'X-MS-CLIENT-PRINCIPAL-IDP': 'google',
        }
    )

    assert identity.provider_key == 'app_service'
    assert identity.issuer == 'app_service:google'
    assert identity.subject_id == 'google-user-1'
    assert identity.display_name == 'Jane Doe'
    assert identity.email == 'jane@example.com'


def test_conflicting_identity_claim_values_are_rejected() -> None:
    payload = _fixture()
    payload['claims'].append(
        {
            'typ': 'http://schemas.microsoft.com/identity/claims/objectidentifier',
            'val': '44444444-4444-4444-4444-444444444444',
        }
    )

    with pytest.raises(IdentityAuthenticationError, match='conflicting values'):
        _resolve({'X-MS-CLIENT-PRINCIPAL': _encode(payload)})
