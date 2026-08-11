import pytest

from atlanticus.web.identity.configuration import resolve_identity_provider_key
from atlanticus.web.identity.errors import IdentityConfigurationError


def test_identity_provider_key_is_required() -> None:
    with pytest.raises(IdentityConfigurationError, match='Missing required environment variable'):
        resolve_identity_provider_key({})


def test_identity_provider_key_must_be_normalized() -> None:
    with pytest.raises(IdentityConfigurationError, match='Invalid identity provider key'):
        resolve_identity_provider_key({'ATLANTICUS_IDENTITY_PROVIDER': ' Local '})


def test_identity_provider_key_returns_selected_provider() -> None:
    assert resolve_identity_provider_key({'ATLANTICUS_IDENTITY_PROVIDER': 'local'}) == 'local'
