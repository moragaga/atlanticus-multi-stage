# Superficie pública mínima del adapter App Service.

from atlanticus.web.identity.app_service.provider import AppServiceIdentityProvider


def create_app_service_identity_provider() -> AppServiceIdentityProvider:
    return AppServiceIdentityProvider()


__all__ = ['AppServiceIdentityProvider', 'create_app_service_identity_provider']
