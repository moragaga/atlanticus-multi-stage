from flask import Flask, request

import atlanticus.web.identity.local.provider as provider_module
from atlanticus.web.identity.local import LocalIdentityProvider, create_local_identity_provider


def test_local_provider_selects_one_persona_per_provider_startup(monkeypatch) -> None:
    monkeypatch.setattr(provider_module.secrets, 'choice', lambda values: values[1])
    provider = create_local_identity_provider()
    server = Flask(__name__)

    with server.test_request_context('/'):
        first = provider.resolve(request)
        second = provider.resolve(request)

    assert first.provider_key == 'local'
    assert first.issuer == 'atlanticus-local'
    assert first.subject_id == 'local:jane-doe'
    assert second.subject_id == first.subject_id


def test_local_provider_can_select_each_supported_persona(monkeypatch) -> None:
    selected = []

    def choose(values):
        value = values[len(selected)]
        selected.append(value)
        return value

    monkeypatch.setattr(provider_module.secrets, 'choice', choose)

    assert create_local_identity_provider()._subject_id == 'local:john-doe'
    assert create_local_identity_provider()._subject_id == 'local:jane-doe'


def test_local_provider_is_not_production_ready() -> None:
    assert LocalIdentityProvider().production_ready is False
