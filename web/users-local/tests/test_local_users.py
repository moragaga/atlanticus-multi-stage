from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.users.local import create_local_users_source


def test_local_source_resolves_john_as_local_and_jane_as_administrator() -> None:
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
    assert jane is not None
    assert jane.display_name == 'Jane Doe'
    assert jane.profile_key == 'administrator'
