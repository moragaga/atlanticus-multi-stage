from types import SimpleNamespace

import pytest

from ada.compositions.web_bootstrap import (
    AdaConfigurationBackends,
    synchronize_ada_access_projections,
)


class FakeWorkflow:
    def __init__(self, *, source_revision: str | None, active_source_revision: str | None) -> None:
        self.source_revision = source_revision
        self.active_source_revision = active_source_revision
        self.projected: list[str] = []

    def get_status(self):
        return SimpleNamespace(
            source_revision=self.source_revision,
            active_source_revision=self.active_source_revision,
        )

    def project(self, expected_source_revision: str) -> None:
        self.projected.append(expected_source_revision)


def _configuration() -> AdaConfigurationBackends:
    return AdaConfigurationBackends(
        users_source=object(),
        users_projection=object(),
        users_discovered=object(),
        navigation_source=object(),
        navigation_projection=object(),
        tools_source=object(),
        tools_projection=object(),
    )


def test_synchronization_projects_users_before_navigation_when_sources_changed(monkeypatch) -> None:
    users = FakeWorkflow(source_revision='users-r2', active_source_revision='users-r1')
    navigation = FakeWorkflow(source_revision='nav-r3', active_source_revision=None)
    order: list[str] = []

    def users_factory(**kwargs):
        del kwargs
        original_project = users.project

        def project(revision: str) -> None:
            order.append('users')
            original_project(revision)

        users.project = project
        return users

    def navigation_factory(**kwargs):
        del kwargs
        original_project = navigation.project

        def project(revision: str) -> None:
            order.append('navigation')
            original_project(revision)

        navigation.project = project
        return navigation

    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.synchronization.UsersProjectionWorkflow',
        users_factory,
    )
    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.synchronization.NavigationProjectionWorkflow',
        navigation_factory,
    )

    result = synchronize_ada_access_projections(configuration=_configuration())

    assert order == ['users', 'navigation']
    assert users.projected == ['users-r2']
    assert navigation.projected == ['nav-r3']
    assert result.users_source_revision == 'users-r2'
    assert result.navigation_source_revision == 'nav-r3'
    assert result.users_projected is True
    assert result.navigation_projected is True


def test_synchronization_is_noop_when_active_projections_match_sources(monkeypatch) -> None:
    users = FakeWorkflow(source_revision='users-r1', active_source_revision='users-r1')
    navigation = FakeWorkflow(source_revision='nav-r1', active_source_revision='nav-r1')
    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.synchronization.UsersProjectionWorkflow',
        lambda **kwargs: users,
    )
    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.synchronization.NavigationProjectionWorkflow',
        lambda **kwargs: navigation,
    )

    result = synchronize_ada_access_projections(configuration=_configuration())

    assert users.projected == []
    assert navigation.projected == []
    assert result.users_projected is False
    assert result.navigation_projected is False


def test_synchronization_accepts_missing_sources(monkeypatch) -> None:
    users = FakeWorkflow(source_revision=None, active_source_revision=None)
    navigation = FakeWorkflow(source_revision=None, active_source_revision=None)
    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.synchronization.UsersProjectionWorkflow',
        lambda **kwargs: users,
    )
    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.synchronization.NavigationProjectionWorkflow',
        lambda **kwargs: navigation,
    )

    result = synchronize_ada_access_projections(configuration=_configuration())

    assert result.users_source_revision is None
    assert result.navigation_source_revision is None
    assert result.users_projected is False
    assert result.navigation_projected is False
    assert users.projected == []
    assert navigation.projected == []


def test_synchronization_projects_available_source_when_other_is_missing(monkeypatch) -> None:
    users = FakeWorkflow(source_revision=None, active_source_revision=None)
    navigation = FakeWorkflow(source_revision='nav-r1', active_source_revision=None)
    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.synchronization.UsersProjectionWorkflow',
        lambda **kwargs: users,
    )
    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.synchronization.NavigationProjectionWorkflow',
        lambda **kwargs: navigation,
    )

    result = synchronize_ada_access_projections(configuration=_configuration())

    assert result.users_source_revision is None
    assert result.navigation_source_revision == 'nav-r1'
    assert result.users_projected is False
    assert result.navigation_projected is True
    assert users.projected == []
    assert navigation.projected == ['nav-r1']


def test_synchronization_rejects_empty_source_revision(monkeypatch) -> None:
    users = FakeWorkflow(source_revision=' ', active_source_revision=None)
    monkeypatch.setattr(
        'ada.compositions.web_bootstrap.synchronization.UsersProjectionWorkflow',
        lambda **kwargs: users,
    )

    with pytest.raises(ValueError, match='Users SharePoint configuration revision'):
        synchronize_ada_access_projections(configuration=_configuration())


def test_synchronization_rejects_empty_actor() -> None:
    with pytest.raises(TypeError, match='actor must be non-empty text'):
        synchronize_ada_access_projections(configuration=_configuration(), actor=' ')
