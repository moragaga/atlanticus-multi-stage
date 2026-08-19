from atlanticus.web.users.activity.adapters import (
    COSMOS_USER_ACTIVITY_PAYLOAD_PATH,
    COSMOS_USER_ACTIVITY_RECORD_TYPE,
    COSMOS_USER_ACTIVITY_STORAGE_SCHEMA_VERSION,
    CosmosUserActivityClient,
    CosmosUserActivityPatchOperationFactory,
    CosmosUserActivityRepository,
    CosmosUserActivitySettings,
    InMemoryUserActivityRepository,
)
from atlanticus.web.users.activity.contracts import UserActivityRepository
from atlanticus.web.users.activity.models import (
    RouteActivity,
    Screen,
    UserActivityDocument,
    UserActivityEvent,
    UserActivityEventType,
    Viewport,
)
from atlanticus.web.users.activity.module import (
    USER_ACTIVITY_ASSET_LAYER,
    USER_ACTIVITY_ENDPOINT,
    USER_ACTIVITY_SERVICE_KEY,
    UserActivityRouteResolverFactory,
    UserActivityUserProvider,
    create_user_activity_module,
)
from atlanticus.web.users.activity.requirements import (
    USER_ACTIVITY_COSMOS_REQUIREMENTS,
    UserActivityCosmosContainerRequirement,
)
from atlanticus.web.users.activity.routes import (
    ActivityRouteIdentity,
    PathnameActivityRouteResolver,
    UserActivityRouteResolver,
)
from atlanticus.web.users.activity.services import UserActivityService

__all__ = [
    'ActivityRouteIdentity',
    'COSMOS_USER_ACTIVITY_PAYLOAD_PATH',
    'COSMOS_USER_ACTIVITY_RECORD_TYPE',
    'COSMOS_USER_ACTIVITY_STORAGE_SCHEMA_VERSION',
    'CosmosUserActivityClient',
    'CosmosUserActivityPatchOperationFactory',
    'CosmosUserActivityRepository',
    'CosmosUserActivitySettings',
    'InMemoryUserActivityRepository',
    'PathnameActivityRouteResolver',
    'RouteActivity',
    'Screen',
    'USER_ACTIVITY_ASSET_LAYER',
    'USER_ACTIVITY_COSMOS_REQUIREMENTS',
    'USER_ACTIVITY_ENDPOINT',
    'USER_ACTIVITY_SERVICE_KEY',
    'UserActivityCosmosContainerRequirement',
    'UserActivityDocument',
    'UserActivityEvent',
    'UserActivityEventType',
    'UserActivityRepository',
    'UserActivityRouteResolver',
    'UserActivityRouteResolverFactory',
    'UserActivityService',
    'UserActivityUserProvider',
    'Viewport',
    'create_user_activity_module',
]
