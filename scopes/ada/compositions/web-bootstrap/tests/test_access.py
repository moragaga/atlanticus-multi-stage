from ada.compositions.web_bootstrap.access import BootstrapAdminUsersSource
from atlanticus.web.identity.models import AuthenticatedIdentity
from atlanticus.web.users.models import ResolvedUserRecord
from atlanticus.web.users.profiles import ADMINISTRATOR_PROFILE_KEY, GUEST_PROFILE_KEY
from atlanticus.web.users.source import UsersSource


class RecordingUsersSource(UsersSource):
    def __init__(self, record: ResolvedUserRecord | None) -> None:
        self.record = record
        self.identities: list[AuthenticatedIdentity] = []

    def resolve(self, identity: AuthenticatedIdentity) -> ResolvedUserRecord | None:
        self.identities.append(identity)
        return self.record


def _identity(email: str | None = 'admin@example.com') -> AuthenticatedIdentity:
    return AuthenticatedIdentity(
        provider_key='app_service',
        issuer='entra',
        subject_id='subject-1',
        display_name='Admin User',
        email=email,
    )


def _guest_record() -> ResolvedUserRecord:
    return ResolvedUserRecord(
        user_id='user-1',
        subject_id='subject-1',
        display_name='Admin User',
        email='admin@example.com',
        enabled=True,
        profile_key=GUEST_PROFILE_KEY,
        pending=True,
    )


def test_bootstrap_admin_promotes_only_effective_record_and_preserves_pending() -> None:
    source = RecordingUsersSource(_guest_record())
    bypass = BootstrapAdminUsersSource(source=source, principal_email='ADMIN@example.com')

    resolved = bypass.resolve(_identity())

    assert resolved is not None
    assert resolved.profile_key == ADMINISTRATOR_PROFILE_KEY
    assert resolved.pending is True
    assert source.record is not None
    assert source.record.profile_key == GUEST_PROFILE_KEY
    assert source.record.pending is True


def test_bootstrap_admin_does_not_promote_different_or_missing_email() -> None:
    record = _guest_record()
    source = RecordingUsersSource(record)
    bypass = BootstrapAdminUsersSource(source=source, principal_email='admin@example.com')

    mismatch = bypass.resolve(_identity('other@example.com'))
    missing = bypass.resolve(_identity(None))

    assert mismatch is record
    assert missing is record


def test_bootstrap_admin_keeps_existing_administrator_record() -> None:
    record = _guest_record()
    admin = ResolvedUserRecord(
        user_id=record.user_id,
        subject_id=record.subject_id,
        display_name=record.display_name,
        email=record.email,
        enabled=True,
        profile_key=ADMINISTRATOR_PROFILE_KEY,
        pending=False,
    )
    source = RecordingUsersSource(admin)
    bypass = BootstrapAdminUsersSource(source=source, principal_email='admin@example.com')

    assert bypass.resolve(_identity()) is admin
