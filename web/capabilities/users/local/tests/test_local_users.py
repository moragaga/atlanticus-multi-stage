from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.users.local import create_local_users_source
from atlanticus.web.users.profiles import has_full_access


def test_local_source_resolves_john_and_jane_as_full_access_local_users() -> None:
    source = create_local_users_source()

    john = source.resolve(
        AuthenticatedIdentity(
            provider_key='local',
            issuer='atlanticus-local',
            subject_id='local:john-doe',
        )
    )
    jane = source.resolve(
        AuthenticatedIdentity(
            provider_key='local',
            issuer='atlanticus-local',
            subject_id='local:jane-doe',
        )
    )

    assert john is not None
    assert john.display_name == 'John Doe'
    assert john.profile_key == 'local'
    assert has_full_access(john.profile_key) is True
    assert jane is not None
    assert jane.display_name == 'Jane Doe'
    assert jane.profile_key == 'local'
    assert has_full_access(jane.profile_key) is True


def test_local_persona_colors_are_fixed_independently_from_profile() -> None:
    source = create_local_users_source()
    john = source.resolve(
        AuthenticatedIdentity(
            provider_key='local', issuer='atlanticus-local', subject_id='local:john-doe'
        )
    )
    jane = source.resolve(
        AuthenticatedIdentity(
            provider_key='local', issuer='atlanticus-local', subject_id='local:jane-doe'
        )
    )

    assert john.avatar_background_color == '#3778C2'
    assert john.avatar_text_color == '#FFFFFF'
    assert jane.avatar_background_color == '#C85D91'
    assert jane.avatar_text_color == '#FFFFFF'
