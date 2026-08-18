from __future__ import annotations

# Espejo pedagógico: Implementa tracking funcional de usuarios: identidad, perfil observado, rutas estables, resolución de pantalla y tiempo activo.

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

from atlanticus.web.users.activity.errors import UsersActivityError


@dataclass(frozen=True, slots=True)
class ActivityRouteIdentity:
    route_key: str
    pathname: str
    is_application_home: bool = False

    def __post_init__(self) -> None:
        route_key = self.route_key.strip()
        pathname = normalize_pathname(self.pathname)
        if not route_key:
            raise UsersActivityError('Activity route key must not be empty')
        object.__setattr__(self, 'route_key', route_key)
        object.__setattr__(self, 'pathname', pathname)


class UserActivityRouteResolver(Protocol):
    def resolve(self, pathname: str) -> ActivityRouteIdentity: ...


class PathnameActivityRouteResolver:
    def __init__(self, *, home_pathname: str = '/') -> None:
        self._home_pathname = normalize_pathname(home_pathname)

    def resolve(self, pathname: str) -> ActivityRouteIdentity:
        normalized = normalize_pathname(pathname)
        return ActivityRouteIdentity(
            route_key=normalized,
            pathname=normalized,
            is_application_home=normalized == self._home_pathname,
        )


def normalize_pathname(value: str) -> str:
    raw = value.strip() or '/'
    parsed = urlsplit(raw)
    path = parsed.path or '/'
    if not path.startswith('/'):
        path = f'/{path}'
    if len(path) > 1:
        path = path.rstrip('/')
    return path[:512]
