import pytest

from atlanticus.web.users.cosmos.models import (
    ProfileCatalogDocument,
    UserDocument,
    UserLookupDocument,
    UsersStateDocument,
)
from atlanticus.web.users.errors import UsersDefinitionError
from atlanticus.web.users.profiles import ProfileDefinition


def test_user_document_derives_partition_and_normalized_email() -> None:
    user = UserDocument(
        user_id='user-1',
        display_name='Jane Doe',
        email=' Jane.Doe@Example.COM ',
        profile_key='Operator',
        enabled=True,
        pending=False,
        origin='projection',
    )

    assert user.partition_key == 'user:user-1'
    assert user.email == 'Jane.Doe@Example.COM'
    assert user.email_normalized == 'jane.doe@example.com'
    assert user.profile_key == 'operator'


def test_projected_user_may_be_unbound_to_identity() -> None:
    user = UserDocument(
        user_id='user-1',
        display_name='Jane Doe',
        profile_key='operator',
        enabled=True,
        pending=False,
        origin='projection',
    )

    assert user.issuer is None
    assert user.subject_id is None


def test_issuer_and_subject_must_coexist() -> None:
    with pytest.raises(UsersDefinitionError, match='must coexist'):
        UserDocument(
            user_id='user-1',
            display_name='Jane Doe',
            profile_key='operator',
            enabled=True,
            pending=False,
            origin='projection',
            issuer='issuer',
        )


def test_identity_origin_must_be_pending() -> None:
    with pytest.raises(UsersDefinitionError, match='must be pending'):
        UserDocument(
            user_id='user-1',
            display_name='Jane Doe',
            profile_key='guest',
            enabled=True,
            pending=False,
            origin='identity',
            issuer='issuer',
            subject_id='oid-1',
        )


def test_lookup_uses_lookup_key_as_partition() -> None:
    lookup = UserLookupDocument(
        kind='identity',
        lookup_key='identity:' + ('a' * 64),
        user_id='user-1',
    )

    assert lookup.id == 'identity'
    assert lookup.partition_key == lookup.lookup_key


def test_state_and_catalog_have_fixed_document_identity() -> None:
    state = UsersStateDocument(source_revision='revision-1', projection_status='READY')
    catalog = ProfileCatalogDocument(
        source_revision='revision-1',
        administrator_color='#112233',
        custom_profiles=(
            ProfileDefinition(key='operator', label='Operador', color='#445566'),
        ),
    )

    assert state.partition_key == 'system'
    assert state.projection_status == 'ready'
    assert catalog.partition_key == 'profiles'
