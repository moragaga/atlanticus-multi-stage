from atlanticus.web.identity.app_service import create_app_service_identity_provider
from atlanticus.web.identity.configuration import resolve_identity_provider_key
from atlanticus.web.identity.errors import IdentityConfigurationError
from atlanticus.web.identity.local import create_local_identity_provider
from atlanticus.web.identity.provider import IdentityProvider


def build_identity_provider() -> IdentityProvider:
    provider_key = resolve_identity_provider_key()
    if provider_key == 'local':
        return create_local_identity_provider()
    if provider_key == 'app_service':
        return create_app_service_identity_provider()
    raise IdentityConfigurationError(
        f'Unsupported identity provider for Integrated Operations: {provider_key!r}'
    )
