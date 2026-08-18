from __future__ import annotations

# Espejo pedagógico: Implementa tracking funcional de usuarios: identidad, perfil observado, rutas estables, resolución de pantalla y tiempo activo.

from datetime import UTC, datetime

from atlanticus.web.users.activity.contracts import UserActivityRepository
from atlanticus.web.users.activity.errors import UsersActivityConflictError, UsersActivityError
from atlanticus.web.users.activity.models import (
    UserActivityDocument,
    UserActivityEvent,
    build_activity_document_id,
)
from atlanticus.web.users.activity.routes import UserActivityRouteResolver
from atlanticus.web.users.models import EffectiveUser


class UserActivityService:
    def __init__(
        self,
        *,
        repository: UserActivityRepository,
        application_key: str,
        route_resolver: UserActivityRouteResolver,
        max_active_delta_seconds: int = 600,
        max_routes: int = 64,
    ) -> None:
        application_key = application_key.strip()
        if not application_key:
            raise UsersActivityError('User activity application key must not be empty')
        if max_active_delta_seconds < 1 or max_routes < 1:
            raise UsersActivityError('User activity limits must be positive')
        self._repository = repository
        self._application_key = application_key
        self._route_resolver = route_resolver
        self._max_active_delta_seconds = max_active_delta_seconds
        self._max_routes = max_routes

    def track(
        self,
        *,
        user: EffectiveUser,
        event: UserActivityEvent,
        now: datetime | None = None,
    ) -> dict[str, object]:
        if user.is_local:
            return {'status': 'local_identity', 'tracked': False}
        if not user.enabled:
            return {'status': 'disabled_user', 'tracked': False}
        occurred_at = (now or datetime.now(UTC)).astimezone(UTC)
        route = self._route_resolver.resolve(event.pathname)
        document_id = build_activity_document_id(
            application_key=self._application_key,
            user_id=user.user_id,
            client_session_id=event.client_session_id,
        )
        for attempt in range(2):
            found = self._repository.find(document_id)
            if found is None:
                document = UserActivityDocument.create(
                    application_key=self._application_key,
                    user=user,
                    event=event,
                    route=route,
                    now=occurred_at,
                )
                try:
                    self._repository.create(document)
                except UsersActivityConflictError:
                    if attempt == 0:
                        continue
                    raise
                return {'status': 'registered', 'tracked': True}
            existing, etag = found
            updated = existing.apply_event(
                user=user,
                event=event,
                route=route,
                now=occurred_at,
                max_active_delta_seconds=self._max_active_delta_seconds,
                max_routes=self._max_routes,
            )
            if updated is existing:
                return {'status': 'duplicate', 'tracked': False}
            try:
                self._repository.replace(updated, etag=etag)
            except UsersActivityConflictError:
                if attempt == 0:
                    continue
                raise
            return {'status': 'updated', 'tracked': True}
        raise UsersActivityError('User activity event could not be persisted')
