import pytest

from ada.compositions.web_deployment.access import (
    resolve_bootstrap_admin_principal,
    resolve_deployment_environment,
)
from atlanticus.web.environment import EnvironmentReader, WebEnvironment
from atlanticus.web.errors import WebConfigurationError


def test_deployment_environment_uses_atlanticus_environment_only() -> None:
    assert resolve_deployment_environment(EnvironmentReader({})) is WebEnvironment.LOCAL
    assert (
        resolve_deployment_environment(EnvironmentReader({'ATLANTICUS_ENVIRONMENT': 'production'}))
        is WebEnvironment.PRODUCTION
    )


def test_local_ignores_bootstrap_admin_value_entirely() -> None:
    reader = EnvironmentReader({'ATLANTICUS_BOOTSTRAP_ADMIN': 'not-an-email'})

    assert resolve_bootstrap_admin_principal(reader, WebEnvironment.LOCAL) is None


def test_production_bootstrap_admin_supports_off_or_normalized_email() -> None:
    assert (
        resolve_bootstrap_admin_principal(EnvironmentReader({}), WebEnvironment.PRODUCTION) is None
    )
    assert (
        resolve_bootstrap_admin_principal(
            EnvironmentReader({'ATLANTICUS_BOOTSTRAP_ADMIN': 'OFF'}),
            WebEnvironment.PRODUCTION,
        )
        is None
    )
    assert (
        resolve_bootstrap_admin_principal(
            EnvironmentReader({'ATLANTICUS_BOOTSTRAP_ADMIN': 'Admin.User@Example.COM'}),
            WebEnvironment.PRODUCTION,
        )
        == 'admin.user@example.com'
    )


@pytest.mark.parametrize('value', [' ', 'admin', ' admin@example.com', 'admin@example.com '])
def test_production_rejects_invalid_bootstrap_admin(value: str) -> None:
    with pytest.raises(WebConfigurationError, match='ATLANTICUS_BOOTSTRAP_ADMIN'):
        resolve_bootstrap_admin_principal(
            EnvironmentReader({'ATLANTICUS_BOOTSTRAP_ADMIN': value}),
            WebEnvironment.PRODUCTION,
        )
