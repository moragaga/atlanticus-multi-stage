import pytest

from ada_application_base.identity import build_identity_provider
from atlanticus.web.identity.errors import IdentityConfigurationError


def test_local_identity_provider_is_reused(monkeypatch) -> None:
    monkeypatch.setenv('ATLANTICUS_IDENTITY_PROVIDER', 'local')

    assert build_identity_provider().key == 'local'


def test_app_service_identity_provider_is_reused(monkeypatch) -> None:
    monkeypatch.setenv('ATLANTICUS_IDENTITY_PROVIDER', 'app_service')

    provider = build_identity_provider()

    assert provider.key == 'app_service'
    assert provider.production_ready is True


def test_unknown_identity_provider_is_rejected(monkeypatch) -> None:
    monkeypatch.setenv('ATLANTICUS_IDENTITY_PROVIDER', 'unsupported')

    with pytest.raises(IdentityConfigurationError, match='Unsupported identity provider'):
        build_identity_provider()
