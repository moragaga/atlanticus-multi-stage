import pytest

from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.users.cosmos.keys import email_lookup_key, identity_lookup_key, pending_user_id
from atlanticus.web.users.cosmos.models import (
    ProfileCatalogDocument,
    UserDocument,
    UserLookupDocument,
    UsersStateDocument,
)
from atlanticus.web.users.cosmos.profiles import UsersCosmosProfileCache
from atlanticus.web.users.cosmos.source import UsersCosmosSource
from atlanticus.web.users.errors import UsersIdentityConflictError, UsersSourceUnavailableError
from atlanticus.web.users.profiles import ProfileDefinition

from .fakes import FakeUsersCosmosGateway


@pytest.fixture
def identity() -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        provider_key='app_service',
        issuer='https://issuer.example/tenant',
        subject_id='oid-1',
        display_name='John Doe',
        email='john.doe@example.com',
    )


def _source(
    *,
    users: tuple[UserDocument, ...] = (),
    lookups: tuple[UserLookupDocument, ...] = (),
) -> tuple[UsersCosmosSource, FakeUsersCosmosGateway]:
    gateway = FakeUsersCosmosGateway(
        state=UsersStateDocument(source_revision='revision-1', projection_status='ready'),
        catalog=ProfileCatalogDocument(
            source_revision='revision-1',
            administrator_background_color='#673AB7',
            custom_profiles=(
                ProfileDefinition(key='operator', label='Operador', background_color='#445566'),
            ),
        ),
        users=users,
        lookups=lookups,
    )
    cache = UsersCosmosProfileCache(gateway)
    return UsersCosmosSource(gateway=gateway, profiles=cache), gateway


def test_resolves_known_user_by_identity_lookup(identity: AuthenticatedIdentity) -> None:
    user = UserDocument(
        user_id='user-1',
        issuer=identity.issuer,
        subject_id=identity.subject_id,
        display_name='John Doe',
        email=identity.email,
        profile_key='operator',
        enabled=True,
        pending=False,
        origin='projection',
        source_revision='revision-1',
    )
    lookup = UserLookupDocument(
        kind='identity',
        lookup_key=identity_lookup_key(issuer=identity.issuer, subject_id=identity.subject_id),
        user_id=user.user_id,
    )
    source, _ = _source(users=(user,), lookups=(lookup,))

    resolved = source.resolve(identity)

    assert resolved.user_id == 'user-1'
    assert resolved.profile_key == 'operator'
    assert resolved.pending is False


def test_reconciles_unbound_projected_user_by_email(identity: AuthenticatedIdentity) -> None:
    user = UserDocument(
        user_id='user-1',
        display_name='John Doe',
        email=identity.email,
        profile_key='operator',
        enabled=True,
        pending=False,
        origin='projection',
        source_revision='revision-1',
    )
    email_lookup = UserLookupDocument(
        kind='email',
        lookup_key=email_lookup_key(identity.email or ''),
        user_id=user.user_id,
    )
    source, gateway = _source(users=(user,), lookups=(email_lookup,))

    resolved = source.resolve(identity)
    identity_key = identity_lookup_key(issuer=identity.issuer, subject_id=identity.subject_id)

    assert resolved.user_id == user.user_id
    assert gateway.lookups[identity_key].user_id == user.user_id


def test_email_does_not_reconcile_user_bound_to_other_identity(
    identity: AuthenticatedIdentity,
) -> None:
    user = UserDocument(
        user_id='user-1',
        issuer=identity.issuer,
        subject_id='other-oid',
        display_name='John Doe',
        email=identity.email,
        profile_key='operator',
        enabled=True,
        pending=False,
        origin='projection',
    )
    email_lookup = UserLookupDocument(
        kind='email',
        lookup_key=email_lookup_key(identity.email or ''),
        user_id=user.user_id,
    )
    source, _ = _source(users=(user,), lookups=(email_lookup,))

    with pytest.raises(UsersIdentityConflictError, match='different authenticated identity'):
        source.resolve(identity)


def test_unknown_identity_is_persisted_as_pending_guest(
    identity: AuthenticatedIdentity,
) -> None:
    source, gateway = _source()

    resolved = source.resolve(identity)
    user_id = pending_user_id(identity)

    assert resolved.user_id == user_id
    assert resolved.profile_key == 'guest'
    assert resolved.pending is True
    assert gateway.users[user_id].origin == 'identity'
    assert gateway.users[user_id].pending is True


def test_unknown_identity_is_pending_guest_without_users_projection(
    identity: AuthenticatedIdentity,
) -> None:
    gateway = FakeUsersCosmosGateway(state=None, catalog=None)
    cache = UsersCosmosProfileCache(gateway)
    source = UsersCosmosSource(gateway=gateway, profiles=cache)

    resolved = source.resolve(identity)
    user_id = pending_user_id(identity)

    assert resolved.user_id == user_id
    assert resolved.profile_key == 'guest'
    assert resolved.pending is True
    assert gateway.users[user_id].origin == 'identity'
    assert gateway.catalog_reads == 0


def test_pending_guest_registration_is_idempotent(identity: AuthenticatedIdentity) -> None:
    source, gateway = _source()

    first = source.resolve(identity)
    second = source.resolve(identity)

    assert first.user_id == second.user_id
    assert len(gateway.users) == 1
    assert len(gateway.lookups) == 2


def test_identity_lookup_to_missing_user_is_source_failure(
    identity: AuthenticatedIdentity,
) -> None:
    lookup = UserLookupDocument(
        kind='identity',
        lookup_key=identity_lookup_key(issuer=identity.issuer, subject_id=identity.subject_id),
        user_id='missing-user',
    )
    source, _ = _source(lookups=(lookup,))

    with pytest.raises(UsersSourceUnavailableError, match='missing user'):
        source.resolve(identity)


def test_identity_lookup_is_authoritative_even_if_email_points_elsewhere(
    identity: AuthenticatedIdentity,
) -> None:
    identity_user = UserDocument(
        user_id='user-1',
        issuer=identity.issuer,
        subject_id=identity.subject_id,
        display_name='John Doe',
        email='old@example.com',
        profile_key='operator',
        enabled=True,
        pending=False,
        origin='projection',
    )
    other_user = UserDocument(
        user_id='user-2',
        issuer=identity.issuer,
        subject_id='oid-2',
        display_name='Other User',
        email=identity.email,
        profile_key='operator',
        enabled=True,
        pending=False,
        origin='projection',
    )
    lookups = (
        UserLookupDocument(
            kind='identity',
            lookup_key=identity_lookup_key(
                issuer=identity.issuer,
                subject_id=identity.subject_id,
            ),
            user_id=identity_user.user_id,
        ),
        UserLookupDocument(
            kind='email',
            lookup_key=email_lookup_key(identity.email or ''),
            user_id=other_user.user_id,
        ),
    )
    source, _ = _source(users=(identity_user, other_user), lookups=lookups)

    resolved = source.resolve(identity)

    assert resolved.user_id == identity_user.user_id
