import pytest

from ada.compositions.web_bootstrap import (
    AdaCosmosBindings,
    build_ada_cosmos_requirements,
    ensure_ada_cosmos_infrastructure,
)


def test_bindings_accept_arbitrary_solution_connection_names() -> None:
    bindings = AdaCosmosBindings(
        users='security-store',
        activity='audit-store',
        navigation='configuration-store',
        tools='configuration-store',
    )

    assert bindings.users == 'security-store'
    assert bindings.activity == 'audit-store'


def test_requirements_group_capabilities_by_connection_and_deduplicate_shared_container() -> None:
    bindings = AdaCosmosBindings(
        users='configuration',
        activity='configuration',
        navigation='configuration',
        tools='configuration',
    )

    requirements = build_ada_cosmos_requirements(bindings)['configuration']

    assert [item.container_name for item in requirements] == [
        'users',
        'users_support',
        'user_activity',
        'configuration',
    ]
    assert [(item.partition_key, item.ttl_seconds) for item in requirements] == [
        ('/partition_key', None),
        ('/partition_key', None),
        ('/id', 86_400),
        ('/partition_key', None),
    ]


def test_requirements_can_span_multiple_connections() -> None:
    bindings = AdaCosmosBindings(
        users='identity',
        activity='activity',
        navigation='configuration',
        tools='configuration',
    )

    requirements = build_ada_cosmos_requirements(bindings)

    assert tuple(requirements) == ('identity', 'activity', 'configuration')
    assert [item.container_name for item in requirements['configuration']] == ['configuration']


@pytest.mark.parametrize('field_name', ('users', 'activity', 'navigation', 'tools'))
def test_bindings_reject_empty_connection_names(field_name: str) -> None:
    values = {
        'users': 'one',
        'activity': 'one',
        'navigation': 'one',
        'tools': 'one',
    }
    values[field_name] = ' '

    with pytest.raises(TypeError, match='non-empty text'):
        AdaCosmosBindings(**values)


def test_ensure_ada_cosmos_infrastructure_delegates_local_database_creation(monkeypatch) -> None:
    captured = {}

    def fake_ensure_cosmos_infrastructure(**kwargs):
        captured.update(kwargs)
        return 'result'

    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.provisioning.ensure_cosmos_infrastructure',
        fake_ensure_cosmos_infrastructure,
    )
    connections = {'configuration': object()}
    bindings = AdaCosmosBindings(
        users='configuration',
        activity='configuration',
        navigation='configuration',
        tools='configuration',
    )

    result = ensure_ada_cosmos_infrastructure(
        cosmos_connections=connections,
        bindings=bindings,
        create_databases_if_missing=True,
    )

    assert result == 'result'
    assert captured['cosmos_connections'] is connections
    assert captured['create_databases_if_missing'] is True
    assert [
        requirement.container_name
        for requirement in captured['requirements_by_connection']['configuration']
    ] == ['users', 'users_support', 'user_activity', 'configuration']
