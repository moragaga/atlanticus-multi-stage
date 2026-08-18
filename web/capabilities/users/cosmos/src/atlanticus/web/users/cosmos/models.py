from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from atlanticus.web.users.errors import UsersDefinitionError
from atlanticus.web.users.profiles import ProfileDefinition

USERS_COSMOS_SCHEMA_VERSION = 1
UserOrigin = Literal['projection', 'identity']
LookupKind = Literal['identity', 'email']


def _required(value: str, *, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise UsersDefinitionError(f'{field_name} must not be empty')
    return normalized


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


@dataclass(frozen=True, slots=True)
class UsersStateDocument:
    source_revision: str
    projection_status: str
    projection_revision: str | None = None
    projected_by: str | None = None
    projected_at_utc: str | None = None
    schema_version: int = USERS_COSMOS_SCHEMA_VERSION
    id: str = 'users'
    partition_key: str = 'system'
    type: str = 'users_state'

    def __post_init__(self) -> None:
        if self.schema_version != USERS_COSMOS_SCHEMA_VERSION:
            raise UsersDefinitionError('Users state schema version is not supported')
        object.__setattr__(
            self,
            'source_revision',
            _required(self.source_revision, field_name='Source revision'),
        )
        object.__setattr__(
            self,
            'projection_status',
            _required(self.projection_status, field_name='Projection status').casefold(),
        )
        if self.id != 'users' or self.partition_key != 'system' or self.type != 'users_state':
            raise UsersDefinitionError('Users state document identity is invalid')


@dataclass(frozen=True, slots=True)
class ProfileCatalogDocument:
    source_revision: str
    administrator_color: str
    guest_color: str = '#FF5722'
    custom_profiles: tuple[ProfileDefinition, ...] = ()
    schema_version: int = USERS_COSMOS_SCHEMA_VERSION
    id: str = 'catalog'
    partition_key: str = 'profiles'
    type: str = 'profile_catalog'

    def __post_init__(self) -> None:
        if self.schema_version != USERS_COSMOS_SCHEMA_VERSION:
            raise UsersDefinitionError('Profile catalog schema version is not supported')
        object.__setattr__(
            self,
            'source_revision',
            _required(self.source_revision, field_name='Source revision'),
        )
        if (
            self.id != 'catalog'
            or self.partition_key != 'profiles'
            or self.type != 'profile_catalog'
        ):
            raise UsersDefinitionError('Profile catalog document identity is invalid')


@dataclass(frozen=True, slots=True)
class UserDocument:
    user_id: str
    display_name: str
    profile_key: str
    enabled: bool
    pending: bool
    origin: UserOrigin
    issuer: str | None = None
    subject_id: str | None = None
    email: str | None = None
    email_normalized: str | None = None
    source_revision: str | None = None
    schema_version: int = USERS_COSMOS_SCHEMA_VERSION
    id: str = 'user'
    partition_key: str | None = None
    type: str = 'user'

    def __post_init__(self) -> None:
        from atlanticus.web.users.cosmos.keys import normalize_email, user_partition_key

        if self.schema_version != USERS_COSMOS_SCHEMA_VERSION:
            raise UsersDefinitionError('User schema version is not supported')
        user_id = _required(self.user_id, field_name='User id')
        display_name = _required(self.display_name, field_name='Display name')
        profile_key = _required(self.profile_key, field_name='Profile key').casefold()
        issuer = _optional(self.issuer)
        subject_id = _optional(self.subject_id)
        email = _optional(self.email)
        source_revision = _optional(self.source_revision)
        if (issuer is None) != (subject_id is None):
            raise UsersDefinitionError('User issuer and subject id must coexist')
        normalized_email = normalize_email(email) if email is not None else None
        provided_email_normalized = _optional(self.email_normalized)
        if provided_email_normalized is not None:
            provided_email_normalized = normalize_email(provided_email_normalized)
        if provided_email_normalized not in {None, normalized_email}:
            raise UsersDefinitionError('User normalized email does not match email')
        if self.origin not in {'projection', 'identity'}:
            raise UsersDefinitionError('User origin is invalid')
        if self.origin == 'identity' and (issuer is None or subject_id is None):
            raise UsersDefinitionError('Identity-origin user must have an identity')
        if self.origin == 'identity' and not self.pending:
            raise UsersDefinitionError('Identity-origin user must be pending')
        partition_key = self.partition_key or user_partition_key(user_id)
        if partition_key != user_partition_key(user_id):
            raise UsersDefinitionError('User partition key does not match user id')
        if self.id != 'user' or self.type != 'user':
            raise UsersDefinitionError('User document identity is invalid')
        object.__setattr__(self, 'user_id', user_id)
        object.__setattr__(self, 'display_name', display_name)
        object.__setattr__(self, 'profile_key', profile_key)
        object.__setattr__(self, 'issuer', issuer)
        object.__setattr__(self, 'subject_id', subject_id)
        object.__setattr__(self, 'email', email)
        object.__setattr__(self, 'email_normalized', normalized_email)
        object.__setattr__(self, 'source_revision', source_revision)
        object.__setattr__(self, 'partition_key', partition_key)


@dataclass(frozen=True, slots=True)
class UserLookupDocument:
    kind: LookupKind
    lookup_key: str
    user_id: str
    schema_version: int = USERS_COSMOS_SCHEMA_VERSION
    id: str | None = None
    partition_key: str | None = None
    type: str = 'user_lookup'

    def __post_init__(self) -> None:
        if self.schema_version != USERS_COSMOS_SCHEMA_VERSION:
            raise UsersDefinitionError('User lookup schema version is not supported')
        if self.kind not in {'identity', 'email'}:
            raise UsersDefinitionError('User lookup kind is invalid')
        lookup_key = _required(self.lookup_key, field_name='Lookup key')
        user_id = _required(self.user_id, field_name='Lookup user id')
        expected_prefix = f'{self.kind}:'
        if not lookup_key.startswith(expected_prefix):
            raise UsersDefinitionError('User lookup key does not match lookup kind')
        if self.id not in {None, self.kind}:
            raise UsersDefinitionError('User lookup id is invalid')
        if self.partition_key not in {None, lookup_key}:
            raise UsersDefinitionError('User lookup partition key is invalid')
        if self.type != 'user_lookup':
            raise UsersDefinitionError('User lookup document type is invalid')
        object.__setattr__(self, 'lookup_key', lookup_key)
        object.__setattr__(self, 'user_id', user_id)
        object.__setattr__(self, 'id', self.kind)
        object.__setattr__(self, 'partition_key', lookup_key)
