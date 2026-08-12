from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.users.cosmos.keys import (
    email_lookup_key,
    identity_lookup_key,
    pending_user_id,
)


def test_identity_lookup_is_stable_and_normalizes_issuer() -> None:
    first = identity_lookup_key(issuer=' HTTPS://Issuer.Example/Tenant ', subject_id='OID-1')
    second = identity_lookup_key(issuer='https://issuer.example/tenant', subject_id='OID-1')

    assert first == second
    assert first.startswith('identity:')
    assert len(first.removeprefix('identity:')) == 64


def test_subject_id_remains_exact() -> None:
    lower = identity_lookup_key(issuer='issuer', subject_id='oid-a')
    upper = identity_lookup_key(issuer='issuer', subject_id='OID-A')

    assert lower != upper


def test_email_lookup_normalizes_email() -> None:
    assert email_lookup_key(' User@Example.COM ') == email_lookup_key('user@example.com')


def test_pending_user_id_is_deterministic_for_identity() -> None:
    identity = AuthenticatedIdentity(
        provider_key='app_service',
        issuer='https://issuer.example/tenant',
        subject_id='oid-1',
    )

    assert pending_user_id(identity) == pending_user_id(identity)
    assert pending_user_id(identity).startswith('pending:')
