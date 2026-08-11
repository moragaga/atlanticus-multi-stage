from flask import Flask, request

from atlanticus.web.identity.local import LocalIdentityProvider, create_local_identity_provider


def test_local_provider_is_zero_configuration_and_deterministic() -> None:
    provider = create_local_identity_provider()
    server = Flask(__name__)

    with server.test_request_context('/'):
        identity = provider.resolve(request)

    assert identity.provider_key == 'local'
    assert identity.issuer == 'atlanticus-local'
    assert identity.subject_id == 'local:john-doe'
    assert identity.display_name is None
    assert identity.email is None


def test_local_provider_is_not_production_ready() -> None:
    assert LocalIdentityProvider().production_ready is False
