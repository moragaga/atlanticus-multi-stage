from atlanticus.web.environment import resolve_environment
from atlanticus.web.identity.app_service import create_app_service_identity_provider
from atlanticus.web.identity.local import create_local_identity_provider
from atlanticus.web.identity.provider import IdentityProvider


def build_reference_identity_provider() -> IdentityProvider:
    if resolve_environment().is_local:
        return create_local_identity_provider()
    return create_app_service_identity_provider()
