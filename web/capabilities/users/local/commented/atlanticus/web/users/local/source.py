# Fuente local determinística para desarrollo.
# John Doe representa el root local y Jane Doe representa administrator.
# El adapter entrega profile_key; el catálogo transversal resuelve la definición completa.

from __future__ import annotations

from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.users.models import ResolvedUserRecord
from atlanticus.web.users.profiles import ADMINISTRATOR_PROFILE_KEY, LOCAL_PROFILE_KEY
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
            ),
            'local:jane-doe': ResolvedUserRecord(
                user_id='local-user:jane-doe',
                subject_id='local:jane-doe',
                display_name='Jane Doe',
                email='jane.doe@local.atlanticus',
                enabled=True,
                profile_key=ADMINISTRATOR_PROFILE_KEY,
            ),
        }

    def resolve(self, identity: AuthenticatedIdentity) -> ResolvedUserRecord | None:
        return self._users.get(identity.subject_id)


def create_local_users_source() -> LocalUsersSource:
    return LocalUsersSource()
