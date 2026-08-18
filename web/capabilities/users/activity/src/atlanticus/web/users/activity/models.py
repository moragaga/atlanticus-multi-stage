from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping

from atlanticus.web.users.activity.errors import UsersActivityError
from atlanticus.web.users.activity.routes import ActivityRouteIdentity, normalize_pathname
from atlanticus.web.users.models import EffectiveUser

USER_ACTIVITY_DOCUMENT_TYPE = 'user_activity_session'
USER_ACTIVITY_SCHEMA_VERSION = 2


class UserActivityEventType(StrEnum):
    REGISTER = 'register'
    HEARTBEAT = 'heartbeat'
    HIDDEN = 'hidden'
    VISIBLE = 'visible'
    ROUTE_CHANGED = 'route_changed'
    PAGEHIDE = 'pagehide'


@dataclass(frozen=True, slots=True)
class Viewport:
    width: int
    height: int

    def __post_init__(self) -> None:
        if self.width < 0 or self.height < 0:
            raise UsersActivityError('Viewport dimensions must not be negative')

    @classmethod
    def from_value(cls, value: object) -> Viewport:
        payload = value if isinstance(value, Mapping) else {}
        return cls(
            width=_safe_dimension(payload.get('width')),
            height=_safe_dimension(payload.get('height')),
        )

    def to_document(self) -> dict[str, int]:
        return {'width': self.width, 'height': self.height}


@dataclass(frozen=True, slots=True)
class Screen:
    width: int
    height: int
    pixel_ratio: float

    def __post_init__(self) -> None:
        if self.width < 0 or self.height < 0:
            raise UsersActivityError('Screen dimensions must not be negative')
        if self.pixel_ratio <= 0:
            raise UsersActivityError('Screen pixel ratio must be positive')

    @classmethod
    def from_value(cls, value: object) -> Screen:
        payload = value if isinstance(value, Mapping) else {}
        return cls(
            width=_safe_dimension(payload.get('width')),
            height=_safe_dimension(payload.get('height')),
            pixel_ratio=_safe_ratio(payload.get('pixel_ratio')),
        )

    def to_document(self) -> dict[str, int | float]:
        return {
            'width': self.width,
            'height': self.height,
            'pixel_ratio': self.pixel_ratio,
        }


@dataclass(frozen=True, slots=True)
class RouteActivity:
    pathname: str
    views: int = 0
    active_seconds: int = 0
    is_application_home: bool = False

    def __post_init__(self) -> None:
        if self.views < 0 or self.active_seconds < 0:
            raise UsersActivityError('Route activity values must not be negative')
        object.__setattr__(self, 'pathname', normalize_pathname(self.pathname))

    def add_time(self, seconds: int) -> RouteActivity:
        return replace(self, active_seconds=self.active_seconds + max(0, seconds))

    def add_view(self) -> RouteActivity:
        return replace(self, views=self.views + 1)

    def to_document(self) -> dict[str, object]:
        return {
            'pathname': self.pathname,
            'views': self.views,
            'active_seconds': self.active_seconds,
            'is_application_home': self.is_application_home,
        }

    @classmethod
    def from_value(cls, value: object) -> RouteActivity:
        payload = value if isinstance(value, Mapping) else {}
        return cls(
            pathname=str(payload.get('pathname') or '/'),
            views=_safe_non_negative_int(payload.get('views')),
            active_seconds=_safe_non_negative_int(payload.get('active_seconds')),
            is_application_home=bool(payload.get('is_application_home', False)),
        )


@dataclass(frozen=True, slots=True)
class UserActivityEvent:
    event_id: str
    client_session_id: str
    sequence: int
    event_type: UserActivityEventType
    pathname: str
    previous_pathname: str | None
    visibility_state: str
    viewport: Viewport
    screen: Screen
    client_timestamp_utc: datetime | None = None

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise UsersActivityError('User activity event id must not be empty')
        if not self.client_session_id.strip():
            raise UsersActivityError('User activity client session id must not be empty')
        if self.sequence < 1:
            raise UsersActivityError('User activity sequence must be positive')
        if self.visibility_state not in {'visible', 'hidden'}:
            raise UsersActivityError('User activity visibility state is invalid')
        object.__setattr__(self, 'event_id', self.event_id.strip()[:120])
        object.__setattr__(self, 'client_session_id', self.client_session_id.strip()[:120])
        object.__setattr__(self, 'pathname', normalize_pathname(self.pathname))
        if self.previous_pathname is not None:
            object.__setattr__(
                self,
                'previous_pathname',
                normalize_pathname(self.previous_pathname),
            )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> UserActivityEvent:
        try:
            event_type = UserActivityEventType(str(payload.get('event_type') or ''))
            sequence = int(payload.get('sequence'))
        except (TypeError, ValueError) as error:
            raise UsersActivityError('User activity payload is invalid') from error
        return cls(
            event_id=str(payload.get('event_id') or ''),
            client_session_id=str(payload.get('client_session_id') or ''),
            sequence=sequence,
            event_type=event_type,
            pathname=str(payload.get('pathname') or '/'),
            previous_pathname=(
                str(payload['previous_pathname']) if payload.get('previous_pathname') else None
            ),
            visibility_state=str(payload.get('visibility_state') or 'visible'),
            viewport=Viewport.from_value(payload.get('viewport')),
            screen=Screen.from_value(payload.get('screen')),
            client_timestamp_utc=_parse_optional_datetime(payload.get('client_timestamp_utc')),
        )


@dataclass(frozen=True, slots=True)
class UserActivityDocument:
    id: str
    application_key: str
    client_session_id: str
    user_id: str
    subject_id: str
    email: str
    display_name: str
    profile_key: str
    first_seen_at_utc: datetime
    last_seen_at_utc: datetime
    active_seconds: int
    page_views: int
    visibility_resumes: int
    visibility_state: str
    current_route_key: str
    current_pathname: str
    initial_viewport: Viewport
    last_viewport: Viewport
    initial_screen: Screen
    last_screen: Screen
    routes: Mapping[str, RouteActivity]
    last_sequence: int
    last_event_id: str
    type: str = USER_ACTIVITY_DOCUMENT_TYPE
    schema_version: int = USER_ACTIVITY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for label, value in (
            ('User activity id', self.id),
            ('Application key', self.application_key),
            ('Client session id', self.client_session_id),
            ('User id', self.user_id),
            ('Subject id', self.subject_id),
            ('Profile key', self.profile_key),
            ('Current route key', self.current_route_key),
        ):
            if not value.strip():
                raise UsersActivityError(f'{label} must not be empty')
        if self.first_seen_at_utc.tzinfo is None or self.last_seen_at_utc.tzinfo is None:
            raise UsersActivityError('User activity timestamps must be timezone-aware')
        if self.active_seconds < 0 or self.page_views < 0 or self.visibility_resumes < 0:
            raise UsersActivityError('User activity counters must not be negative')
        if self.visibility_state not in {'visible', 'hidden'}:
            raise UsersActivityError('User activity visibility state is invalid')
        object.__setattr__(self, 'current_pathname', normalize_pathname(self.current_pathname))
        object.__setattr__(self, 'routes', MappingProxyType(dict(self.routes)))

    @classmethod
    def create(
        cls,
        *,
        application_key: str,
        user: EffectiveUser,
        event: UserActivityEvent,
        route: ActivityRouteIdentity,
        now: datetime,
    ) -> UserActivityDocument:
        visible = event.event_type not in {
            UserActivityEventType.HIDDEN,
            UserActivityEventType.PAGEHIDE,
        }
        return cls(
            id=build_activity_document_id(
                application_key=application_key,
                user_id=user.user_id,
                client_session_id=event.client_session_id,
            ),
            application_key=application_key,
            client_session_id=event.client_session_id,
            user_id=user.user_id,
            subject_id=user.subject_id,
            email=user.email or '',
            display_name=user.display_name,
            profile_key=user.profile.key,
            first_seen_at_utc=now.astimezone(UTC),
            last_seen_at_utc=now.astimezone(UTC),
            active_seconds=0,
            page_views=1 if visible else 0,
            visibility_resumes=0,
            visibility_state='visible' if visible else 'hidden',
            current_route_key=route.route_key,
            current_pathname=route.pathname,
            initial_viewport=event.viewport,
            last_viewport=event.viewport,
            initial_screen=event.screen,
            last_screen=event.screen,
            routes={
                route.route_key: RouteActivity(
                    pathname=route.pathname,
                    views=1 if visible else 0,
                    is_application_home=route.is_application_home,
                )
            },
            last_sequence=event.sequence,
            last_event_id=event.event_id,
        )

    def apply_event(
        self,
        *,
        user: EffectiveUser,
        event: UserActivityEvent,
        route: ActivityRouteIdentity,
        now: datetime,
        max_active_delta_seconds: int,
        max_routes: int,
    ) -> UserActivityDocument:
        if event.sequence <= self.last_sequence or event.event_id == self.last_event_id:
            return self
        routes = dict(self.routes)
        active_seconds = self.active_seconds
        page_views = self.page_views
        visibility_resumes = self.visibility_resumes
        current_route_key = self.current_route_key
        visibility_state = self.visibility_state
        closes_segment = self.visibility_state == 'visible' and event.event_type in {
            UserActivityEventType.HEARTBEAT,
            UserActivityEventType.HIDDEN,
            UserActivityEventType.ROUTE_CHANGED,
            UserActivityEventType.PAGEHIDE,
        }
        if closes_segment:
            delta = _active_delta(
                start=self.last_seen_at_utc,
                end=now,
                maximum=max_active_delta_seconds,
            )
            active_seconds += delta
            current = routes.get(
                current_route_key,
                RouteActivity(pathname=self.current_pathname),
            )
            routes[current_route_key] = current.add_time(delta)
        if event.event_type in {
            UserActivityEventType.REGISTER,
            UserActivityEventType.ROUTE_CHANGED,
        }:
            current_route_key = route.route_key
            current = routes.get(
                route.route_key,
                RouteActivity(
                    pathname=route.pathname,
                    is_application_home=route.is_application_home,
                ),
            )
            routes[route.route_key] = current.add_view()
            page_views += 1
            visibility_state = event.visibility_state
        elif event.event_type is UserActivityEventType.VISIBLE:
            if self.visibility_state != 'visible':
                visibility_resumes += 1
            visibility_state = 'visible'
            current_route_key = route.route_key
        elif event.event_type in {
            UserActivityEventType.HIDDEN,
            UserActivityEventType.PAGEHIDE,
        }:
            visibility_state = 'hidden'
        elif event.event_type is UserActivityEventType.HEARTBEAT:
            visibility_state = event.visibility_state
            current_route_key = route.route_key
        routes = _limit_routes(routes, current_route_key=current_route_key, maximum=max_routes)
        current_route = routes.get(
            current_route_key,
            RouteActivity(
                pathname=route.pathname,
                is_application_home=route.is_application_home,
            ),
        )
        return replace(
            self,
            subject_id=user.subject_id,
            email=user.email or '',
            display_name=user.display_name,
            last_seen_at_utc=now.astimezone(UTC),
            active_seconds=active_seconds,
            page_views=page_views,
            visibility_resumes=visibility_resumes,
            visibility_state=visibility_state,
            current_route_key=current_route_key,
            current_pathname=current_route.pathname,
            last_viewport=event.viewport,
            last_screen=event.screen,
            routes=routes,
            last_sequence=event.sequence,
            last_event_id=event.event_id,
        )

    def to_document(self) -> dict[str, object]:
        return {
            'id': self.id,
            'type': self.type,
            'schema_version': self.schema_version,
            'application_key': self.application_key,
            'client_session_id': self.client_session_id,
            'user_id': self.user_id,
            'subject_id': self.subject_id,
            'email': self.email,
            'display_name': self.display_name,
            'profile_key': self.profile_key,
            'first_seen_at_utc': self.first_seen_at_utc.isoformat(),
            'last_seen_at_utc': self.last_seen_at_utc.isoformat(),
            'active_seconds': self.active_seconds,
            'page_views': self.page_views,
            'visibility_resumes': self.visibility_resumes,
            'visibility_state': self.visibility_state,
            'current_route_key': self.current_route_key,
            'current_pathname': self.current_pathname,
            'initial_viewport': self.initial_viewport.to_document(),
            'last_viewport': self.last_viewport.to_document(),
            'initial_screen': self.initial_screen.to_document(),
            'last_screen': self.last_screen.to_document(),
            'routes': {key: value.to_document() for key, value in self.routes.items()},
            'last_sequence': self.last_sequence,
            'last_event_id': self.last_event_id,
        }


def build_activity_document_id(
    *,
    application_key: str,
    user_id: str,
    client_session_id: str,
) -> str:
    raw = f'{application_key.strip()}:{user_id.strip()}:{client_session_id.strip()}'
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _active_delta(*, start: datetime, end: datetime, maximum: int) -> int:
    seconds = max(0, int((end - start).total_seconds()))
    return min(seconds, maximum)


def _limit_routes(
    routes: dict[str, RouteActivity],
    *,
    current_route_key: str,
    maximum: int,
) -> dict[str, RouteActivity]:
    if len(routes) <= maximum:
        return routes
    removable = [key for key in routes if key != current_route_key]
    removable.sort(key=lambda key: (routes[key].views, routes[key].active_seconds, key))
    while len(routes) > maximum and removable:
        routes.pop(removable.pop(0), None)
    return routes


def _safe_dimension(value: object) -> int:
    try:
        return max(0, int(value or 0))
    except TypeError, ValueError:
        return 0


def _safe_non_negative_int(value: object) -> int:
    return _safe_dimension(value)


def _safe_ratio(value: object) -> float:
    try:
        ratio = float(value or 1)
    except TypeError, ValueError:
        return 1.0
    return ratio if ratio > 0 else 1.0


def _parse_optional_datetime(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
