from atlanticus.web.users.cosmos.adapter import CosmosUsersGatewayAdapter
# Espejo pedagógico: Expone la fuente runtime Cosmos y los adapters de proyección/configuración sin acoplar consumidores a detalles internos.

from atlanticus.web.users.cosmos.configuration import (
    CosmosDiscoveredUsersSource,
    CosmosUsersConfigurationSettings,
    CosmosUsersProjectionRepository,
)
from atlanticus.web.users.cosmos.gateway import UsersCosmosGateway
from atlanticus.web.users.cosmos.profiles import CosmosProfileCatalog, UsersCosmosProfileCache
from atlanticus.web.users.cosmos.requirements import USERS_COSMOS_REQUIREMENTS
from atlanticus.web.users.cosmos.source import UsersCosmosSource

__all__ = [
    'CosmosDiscoveredUsersSource',
    'CosmosProfileCatalog',
    'CosmosUsersConfigurationSettings',
    'CosmosUsersGatewayAdapter',
    'CosmosUsersProjectionRepository',
    'USERS_COSMOS_REQUIREMENTS',
    'UsersCosmosGateway',
    'UsersCosmosProfileCache',
    'UsersCosmosSource',
]
