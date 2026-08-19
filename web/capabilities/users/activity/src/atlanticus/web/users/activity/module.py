from __future__ import annotations

from collections.abc import Callable
from typing import Mapping

from flask import Flask, jsonify, request

from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.activity.contracts import UserActivityRepository
from atlanticus.web.users.activity.errors import UsersActivityError
from atlanticus.web.users.activity.models import UserActivityEvent
from atlanticus.web.users.activity.routes import (
    PathnameActivityRouteResolver,
    UserActivityRouteResolver,
)
from atlanticus.web.users.activity.services import UserActivityService
from atlanticus.web.users.models import EffectiveUser

USER_ACTIVITY_SERVICE_KEY = 'atlanticus.web.users.activity.service'
USER_ACTIVITY_ENDPOINT = '/api/user-activity'
USER_ACTIVITY_ASSET_LAYER = AssetLayer(
    name='user-activity',
    load_order=650,
    package='atlanticus.web.users.activity',
    resource_directory='resources',
)
UserActivityUserProvider = Callable[[ServiceRegistry], EffectiveUser]
UserActivityRouteResolverFactory = Callable[[ServiceRegistry], UserActivityRouteResolver]


def create_user_activity_module(
    *,
    repository: UserActivityRepository,
    application_key: str,
    user_provider: UserActivityUserProvider,
    route_resolver_factory: UserActivityRouteResolverFactory | None = None,
) -> WebModule:
    factory = route_resolver_factory or _pathname_route_resolver

    def register_services(services: ServiceRegistry) -> None:
        services.add(
            USER_ACTIVITY_SERVICE_KEY,
            UserActivityService(
                repository=repository,
                application_key=application_key,
                route_resolver=factory(services),
            ),
        )

    def register_routes(server: Flask, services: ServiceRegistry) -> None:
        activity_service = services.require(USER_ACTIVITY_SERVICE_KEY, UserActivityService)

        @server.post(USER_ACTIVITY_ENDPOINT)
        def track_user_activity():
            payload = request.get_json(silent=True)
            if not isinstance(payload, Mapping):
                return jsonify({'status': 'invalid_payload', 'tracked': False}), 400
            try:
                event = UserActivityEvent.from_payload(payload)
            except UsersActivityError:
                return jsonify({'status': 'invalid_payload', 'tracked': False}), 400
            try:
                result = activity_service.track(
                    user=user_provider(services),
                    event=event,
                )
            except UsersActivityError:
                return jsonify({'status': 'unavailable', 'tracked': False}), 503
            return jsonify(result), 200

    return WebModule(
        name='user-activity',
        asset_layers=(USER_ACTIVITY_ASSET_LAYER,),
        register_services=register_services,
        register_routes=register_routes,
    )


def _pathname_route_resolver(_services: ServiceRegistry) -> UserActivityRouteResolver:
    return PathnameActivityRouteResolver()
