from dataclasses import dataclass

import pytest

import atlanticus.web.compositions.runtime_infrastructure.provisioning as provisioning_module
from atlanticus.connectivity.cosmos import CosmosSettings
from atlanticus.web.compositions.runtime_infrastructure import (
    create_cosmos_container_specs,
    ensure_cosmos_infrastructure,
)


@dataclass(frozen=True, slots=True)
class Requirement:
    container_name: str
    partition_key: str
    ttl_seconds: int | None = None


def test_capability_requirements_translate_to_connectivity_specs() -> None:
    specs = create_cosmos_container_specs(
        (
            Requirement('users', '/partition_key'),
            Requirement('user_activity', '/id', 86_400),
        )
    )

    assert tuple(spec.name for spec in specs) == ('users', 'user_activity')
    assert tuple(spec.partition_key_path for spec in specs) == ('/partition_key', '/id')
    assert tuple(spec.default_ttl_seconds for spec in specs) == (None, 86_400)


def test_duplicate_capability_container_names_are_rejected_before_provisioning() -> None:
    with pytest.raises(
        ValueError,
        match='Cosmos container requirements must have unique container names',
    ):
        create_cosmos_container_specs(
            (
                Requirement('users', '/partition_key'),
                Requirement('users', '/other'),
            )
        )


def test_provisioning_uses_solution_connection_binding_without_predefined_names(
    monkeypatch,
) -> None:
    events = []

    class FakeCosmosClient:
        def __init__(self, *, settings):
            self.settings = settings

        def __enter__(self):
            events.append(('open', self.settings.database_name))
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            del exc_type, exc_value, traceback
            events.append(('close', self.settings.database_name))

    class FakeCosmosProvisioner:
        def __init__(self, *, client):
            self.client = client

        def ensure_database(self):
            events.append(('database', self.client.settings.database_name))
            return False

        def ensure_containers(self, specs):
            names = tuple(spec.name for spec in specs)
            events.append(('containers', self.client.settings.database_name, names))
            return names

    monkeypatch.setattr(provisioning_module, 'CosmosClient', FakeCosmosClient)
    monkeypatch.setattr(provisioning_module, 'CosmosProvisioner', FakeCosmosProvisioner)

    result = ensure_cosmos_infrastructure(
        cosmos_connections={
            'solution_configuration': _settings('ada-config'),
            'projection_store': _settings('ada-projections'),
        },
        requirements_by_connection={
            'solution_configuration': (
                Requirement('users', '/partition_key'),
                Requirement('user_activity', '/id', 86_400),
            ),
            'projection_store': (Requirement('tool_projection', '/id'),),
        },
    )

    assert result.databases_created == ()
    assert dict(result.containers_created) == {
        'solution_configuration': ('users', 'user_activity'),
        'projection_store': ('tool_projection',),
    }
    assert ('database', 'ada-config') not in events
    assert ('database', 'ada-projections') not in events


def test_local_bootstrap_can_create_missing_database_before_containers(monkeypatch) -> None:
    events = []

    class FakeCosmosClient:
        def __init__(self, *, settings):
            self.settings = settings

        def __enter__(self):
            events.append('open')
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            del exc_type, exc_value, traceback
            events.append('close')

    class FakeCosmosProvisioner:
        def __init__(self, *, client):
            self.client = client

        def ensure_database(self):
            events.append('database')
            return True

        def ensure_containers(self, specs):
            events.append(('containers', tuple(spec.name for spec in specs)))
            return ('users',)

    monkeypatch.setattr(provisioning_module, 'CosmosClient', FakeCosmosClient)
    monkeypatch.setattr(provisioning_module, 'CosmosProvisioner', FakeCosmosProvisioner)

    result = ensure_cosmos_infrastructure(
        cosmos_connections={'configuration': _local_settings('ada-local')},
        requirements_by_connection={
            'configuration': (Requirement('users', '/partition_key'),),
        },
        create_databases_if_missing=True,
    )

    assert events == ['open', 'database', ('containers', ('users',)), 'close']
    assert result.databases_created == ('configuration',)
    assert dict(result.containers_created) == {'configuration': ('users',)}


def test_unknown_requirement_connection_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown Cosmos connection 'missing' in requirements"):
        ensure_cosmos_infrastructure(
            cosmos_connections={'configuration': _settings('ada-config')},
            requirements_by_connection={
                'missing': (Requirement('users', '/partition_key'),),
            },
        )


def _settings(database_name: str) -> CosmosSettings:
    return CosmosSettings(
        endpoint='https://example.documents.azure.com/',
        key='secret',
        database_name=database_name,
    )


def _local_settings(database_name: str) -> CosmosSettings:
    return CosmosSettings(
        endpoint='http://cosmos-emulator:8081/',
        key='emulator-key',
        database_name=database_name,
        allow_insecure_http=True,
    )
