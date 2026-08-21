from ada.compositions.configuration_manager import manager_principal_from_effective_user
from atlanticus.web.users.models import EffectiveUser
from atlanticus.web.users.profiles import ProfileCatalog


def test_effective_user_maps_to_manager_principal_without_second_identity_model() -> None:
    profile = ProfileCatalog().require('administrator')
    user = EffectiveUser(
        user_id='user-1',
        subject_id='entra:subject-1',
        display_name='Ada Admin',
        email='ada.admin@example.com',
        enabled=True,
        pending=False,
        avatar_text='AA',
        profile=profile,
    )

    principal = manager_principal_from_effective_user(user)

    assert principal.subject_id == 'entra:subject-1'
    assert principal.display_name == 'Ada Admin'
    assert principal.profile_keys == ('administrator',)
    assert principal.is_local is False


def test_local_effective_user_preserves_local_manager_access() -> None:
    profile = ProfileCatalog().require('local')
    user = EffectiveUser(
        user_id='local-user:john-doe',
        subject_id='local:john-doe',
        display_name='John Doe',
        email='john.doe@local.atlanticus',
        enabled=True,
        pending=False,
        avatar_text='JD',
        profile=profile,
        is_local=True,
    )

    principal = manager_principal_from_effective_user(user)

    assert principal.profile_keys == ('local',)
    assert principal.is_local is True
