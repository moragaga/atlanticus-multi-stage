import pytest

from atlanticus.web.users.configuration import (
    UserConfiguration,
    UserProfileConfiguration,
    UsersConfigurationCatalog,
    compose_users_configuration_services,
)
from atlanticus.web.users.configuration.adapters import (
    MemoryDiscoveredUsersSource,
    MemoryUsersConfigurationStore,
    MemoryUsersProjectionRepository,
)
from atlanticus.web.users.configuration.errors import UsersConfigurationSourceError


def _catalog(label: str = 'Operador') -> UsersConfigurationCatalog:
    return UsersConfigurationCatalog(
        administrator_color='#673AB7',
        guest_color='#FF5722',
        profiles=(
            UserProfileConfiguration(
                key='operator',
                label=label,
                color='#123456',
            ),
        ),
        users=(
            UserConfiguration.create(
                display_name='User One',
                email='one@example.com',
                profile_key='operator',
            ),
        ),
    )


def test_validate_publish_project_lifecycle_is_separated() -> None:
    source = MemoryUsersConfigurationStore()
    projection = MemoryUsersProjectionRepository()
    services = compose_users_configuration_services(
        source=source,
        publisher=source,
        projection=projection,
        discovered=MemoryDiscoveredUsersSource(),
        audit_actor_provider=lambda: 'administrator',
    )
    catalog = _catalog()

    validation = services.administration.validate_catalog(catalog)
    assert validation.valid is True
    assert source.fetch_bundle() is None

    publication = services.administration.publish_catalog(
        catalog,
        expected_source_revision=None,
    )
    assert publication.published is True
    assert len(source.list_history()) == 1
    assert projection.load_state() is None

    result = services.projection_workflow.project(publication.source_revision)
    assert result.projected is True
    assert projection.load_state().source_revision == publication.source_revision


def test_republishing_same_content_does_not_create_history_copy() -> None:
    source = MemoryUsersConfigurationStore()
    services = compose_users_configuration_services(
        source=source,
        publisher=source,
        projection=MemoryUsersProjectionRepository(),
        discovered=MemoryDiscoveredUsersSource(),
        audit_actor_provider=lambda: 'administrator',
    )
    catalog = _catalog()

    first = services.administration.publish_catalog(catalog, expected_source_revision=None)
    second = services.administration.publish_catalog(
        catalog,
        expected_source_revision=first.source_revision,
    )

    assert second.published is False
    assert len(source.list_history()) == 1


def test_stale_source_revision_is_rejected() -> None:
    source = MemoryUsersConfigurationStore()
    services = compose_users_configuration_services(
        source=source,
        publisher=source,
        projection=MemoryUsersProjectionRepository(),
        discovered=MemoryDiscoveredUsersSource(),
        audit_actor_provider=lambda: 'administrator',
    )
    first = services.administration.publish_catalog(_catalog(), expected_source_revision=None)

    with pytest.raises(UsersConfigurationSourceError):
        services.administration.publish_catalog(
            _catalog('Nuevo nombre'),
            expected_source_revision='stale',
        )

    assert source.fetch_bundle().revision == first.source_revision
