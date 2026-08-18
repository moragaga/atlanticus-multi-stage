import pytest

from atlanticus.web.users.cosmos.models import ProfileCatalogDocument, UsersStateDocument
from atlanticus.web.users.cosmos.profiles import CosmosProfileCatalog, UsersCosmosProfileCache
from atlanticus.web.users.errors import UsersSourceUnavailableError
from atlanticus.web.users.profiles import ProfileDefinition

from .fakes import FakeUsersCosmosGateway


def _gateway(revision: str = 'revision-1') -> FakeUsersCosmosGateway:
    return FakeUsersCosmosGateway(
        state=UsersStateDocument(source_revision=revision, projection_status='ready'),
        catalog=ProfileCatalogDocument(
            source_revision=revision,
            administrator_color='#112233',
            guest_color='#334455',
            custom_profiles=(
                ProfileDefinition(key='operator', label='Operador', color='#445566'),
            ),
        ),
    )


def test_profile_catalog_is_cached_for_current_revision() -> None:
    gateway = _gateway()
    cache = UsersCosmosProfileCache(gateway)
    profiles = CosmosProfileCatalog(cache)

    cache.ensure_current()
    cache.ensure_current()

    assert profiles.require('operator').label == 'Operador'
    assert profiles.require('administrator').color == '#112233'
    assert profiles.require('guest').color == '#334455'
    assert gateway.state_reads == 2
    assert gateway.catalog_reads == 1


def test_profile_catalog_reloads_when_source_revision_changes() -> None:
    gateway = _gateway()
    cache = UsersCosmosProfileCache(gateway)
    profiles = CosmosProfileCatalog(cache)
    cache.ensure_current()

    gateway.state = UsersStateDocument(source_revision='revision-2', projection_status='ready')
    gateway.catalog = ProfileCatalogDocument(
        source_revision='revision-2',
        administrator_color='#223344',
        custom_profiles=(
            ProfileDefinition(key='operator', label='Operador 2', color='#556677'),
        ),
    )
    cache.ensure_current()

    assert profiles.require('operator').label == 'Operador 2'
    assert profiles.require('administrator').color == '#223344'
    assert gateway.catalog_reads == 2


def test_projection_must_be_ready() -> None:
    gateway = _gateway()
    gateway.state = UsersStateDocument(source_revision='revision-1', projection_status='updating')
    cache = UsersCosmosProfileCache(gateway)

    with pytest.raises(UsersSourceUnavailableError, match='not ready'):
        cache.ensure_current()


def test_catalog_revision_must_match_state() -> None:
    gateway = _gateway()
    gateway.catalog = ProfileCatalogDocument(
        source_revision='revision-0',
        administrator_color='#112233',
    )
    cache = UsersCosmosProfileCache(gateway)

    with pytest.raises(UsersSourceUnavailableError, match='revision is not ready'):
        cache.ensure_current()


def test_state_gateway_failure_becomes_source_unavailable() -> None:
    from atlanticus.web.users.cosmos.errors import UsersCosmosGatewayError

    class BrokenGateway(FakeUsersCosmosGateway):
        def read_state(self) -> UsersStateDocument | None:
            raise UsersCosmosGatewayError('unavailable')

    gateway = BrokenGateway(state=None, catalog=None)
    cache = UsersCosmosProfileCache(gateway)

    with pytest.raises(UsersSourceUnavailableError, match='state is unavailable'):
        cache.ensure_current()
