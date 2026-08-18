from __future__ import annotations

# Espejo pedagógico: Provee las personas locales de prueba. John y Jane conservan colores fijos independientes de su perfil de permisos.

from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.users.models import ResolvedUserRecord
from atlanticus.web.users.profiles import (
    ADMINISTRATOR_PROFILE_KEY,
    LOCAL_JANE_COLOR,
    LOCAL_JOHN_COLOR,
    LOCAL_PROFILE_KEY,
)
from atlanticus.web.users.source import UsersSource


class LocalUsersSource(UsersSource):
    def __init__(self) -> None:
        self._users = {
            'local:john-doe': ResolvedUserRecord(
                user_id='local-user:john-doe',
                subject_id='local:john-doe',
                display_name='John Doe',
                email='john.doe@local.atlanticus',
                enabled=True,
                profile_key=LOCAL_PROFILE_KEY,
                avatar_color=LOCAL_JOHN_COLOR,
                is_local=True,
            ),
            'local:jane-doe': ResolvedUserRecord(
                user_id='local-user:jane-doe',
                subject_id='local:jane-doe',
                display_name='Jane Doe',
                email='jane.doe@local.atlanticus',
                enabled=True,
                profile_key=ADMINISTRATOR_PROFILE_KEY,
                avatar_color=LOCAL_JANE_COLOR,
                is_local=True,
            ),
        }

    def resolve(self, identity: AuthenticatedIdentity) -> ResolvedUserRecord | None:
        return self._users.get(identity.subject_id)


def create_local_users_source() -> LocalUsersSource:
    return LocalUsersSource()
