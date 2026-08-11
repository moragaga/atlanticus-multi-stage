import pytest

from atlanticus.web.environment import WebEnvironment, resolve_environment
from atlanticus.web.errors import WebConfigurationError


def test_environment_defaults_to_local():
    assert resolve_environment({}) is WebEnvironment.LOCAL


def test_environment_accepts_local_and_production():
    assert resolve_environment({'ATLANTICUS_ENVIRONMENT': 'local'}) is WebEnvironment.LOCAL
    assert (
        resolve_environment({'ATLANTICUS_ENVIRONMENT': 'production'}) is WebEnvironment.PRODUCTION
    )


def test_environment_rejects_unknown_value():
    with pytest.raises(WebConfigurationError, match='Invalid ATLANTICUS_ENVIRONMENT'):
        resolve_environment({'ATLANTICUS_ENVIRONMENT': 'dev'})
