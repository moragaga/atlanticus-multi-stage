# Reexporta los adapters y constantes de persistencia que forman la superficie pública Activity.
from atlanticus.web.users.activity.adapters.cosmos import (
    COSMOS_USER_ACTIVITY_PAYLOAD_PATH,
    COSMOS_USER_ACTIVITY_RECORD_TYPE,
    COSMOS_USER_ACTIVITY_STORAGE_SCHEMA_VERSION,
    CosmosUserActivityClient,
    CosmosUserActivityPatchOperationFactory,
    CosmosUserActivityRepository,
    CosmosUserActivitySettings,
)
from atlanticus.web.users.activity.adapters.memory import InMemoryUserActivityRepository

__all__ = [
    'COSMOS_USER_ACTIVITY_PAYLOAD_PATH',
    'COSMOS_USER_ACTIVITY_RECORD_TYPE',
    'COSMOS_USER_ACTIVITY_STORAGE_SCHEMA_VERSION',
    'CosmosUserActivityClient',
    'CosmosUserActivityPatchOperationFactory',
    'CosmosUserActivityRepository',
    'CosmosUserActivitySettings',
    'InMemoryUserActivityRepository',
]
