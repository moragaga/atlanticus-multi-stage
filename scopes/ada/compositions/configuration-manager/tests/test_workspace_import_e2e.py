from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from ada.compositions.configuration_manager.workflows import (
    NavigationManagerWorkflowAdapter,
    NavigationWorkspaceImportAdapter,
    ToolManagerWorkflowAdapter,
    ToolWorkspaceImportAdapter,
    UsersManagerWorkflowAdapter,
    UsersWorkspaceImportAdapter,
)
from ada.configuration.tools import (
    ToolConfigurationBundle,
    ToolConfigurationCatalog,
    compose_tool_configuration_services,
    integrated_operations_configuration_from_manifest,
)
from ada.configuration.tools.adapters import (
    FileToolConfigurationSettings,
    FileToolConfigurationStore,
    SharePointToolConfigurationSettings,
    SharePointToolConfigurationStore,
)
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST
from atlanticus.web.manager import (
    DefaultManagerAuthorizationPolicy,
    ManagerModule,
    ManagerModuleAccess,
    ManagerModuleGroup,
    ManagerModuleRegistry,
    ManagerPrincipal,
    ManagerProjectionCoordinator,
    ManagerSourceConflictError,
)
from atlanticus.web.navigation.configuration import (
    NavigationConfigurationBundle,
    NavigationConfigurationCatalog,
    NavigationLinkConfiguration,
    compose_navigation_configuration_services,
)
from atlanticus.web.navigation.configuration.adapters import (
    FileNavigationConfigurationSettings,
    FileNavigationConfigurationStore,
    SharePointNavigationConfigurationSettings,
    SharePointNavigationConfigurationStore,
)
from atlanticus.web.services import ServiceRegistry
from atlanticus.web.users.configuration import (
    UserConfiguration,
    UserProfileConfiguration,
    UsersConfigurationBundle,
    UsersConfigurationCatalog,
    compose_users_configuration_services,
)
from atlanticus.web.users.configuration.adapters import (
    FileUsersConfigurationSettings,
    FileUsersConfigurationStore,
    SharePointUsersConfigurationSettings,
    SharePointUsersConfigurationStore,
)


class MemorySharePointGateway:
    def __init__(self) -> None:
        self.documents: dict[tuple[str, str], str] = {}
        self.write_count = 0

    def read(self, *, filename: str, relative_path: str) -> str | None:
        return self.documents.get((relative_path, filename))

    def write(self, *, filename: str, relative_path: str, content: str) -> None:
        self.documents[(relative_path, filename)] = content
        self.write_count += 1


class ProjectionProbe:
    def __init__(self) -> None:
        self.write_count = 0

    def load(self):
        return None

    def load_state(self):
        return None

    def save(self, _projection):
        self.write_count += 1
        raise AssertionError('Projection must not be written during workspace import publication')

    def project(self, _bundle, *, actor: str):
        self.write_count += 1
        raise AssertionError(
            f'Projection must not be written during workspace import publication by {actor}'
        )

    def health_check(self) -> bool:
        return True


class EmptyDiscoveredUsers:
    def list_discovered(self):
        return ()


@dataclass(slots=True)
class ModuleHarness:
    key: str
    local_store: object
    sharepoint_store: object
    coordinator: ManagerProjectionCoordinator
    principal: ManagerPrincipal
    projection: ProjectionProbe
    local_current_document: dict[str, object]
    external_document: dict[str, object]


def _tool_catalog(label: str) -> ToolConfigurationCatalog:
    configured = integrated_operations_configuration_from_manifest(INTEGRATED_OPERATIONS_MANIFEST)
    return ToolConfigurationCatalog((replace(configured, display_name=label),))


def _users_catalog(label: str) -> UsersConfigurationCatalog:
    profile = UserProfileConfiguration(
        key='operator',
        label=label,
        background_color='#445566',
    )
    return UsersConfigurationCatalog(
        profiles=(profile,),
        users=(
            UserConfiguration.create(
                display_name=f'{label} User',
                email=f'{label.casefold().replace(" ", ".")}@example.com',
                profile_key=profile.key,
            ),
        ),
    )


def _navigation_catalog(label: str) -> NavigationConfigurationCatalog:
    return NavigationConfigurationCatalog(
        links=(
            NavigationLinkConfiguration(
                key='home',
                label=label,
                href='/',
            ),
        )
    )


def _manager(
    *,
    key: str,
    workflow: object,
    workspace_import: object,
) -> tuple[ManagerProjectionCoordinator, ManagerPrincipal]:
    access_key = f'{key}.manage'
    module = ManagerModule(
        key=key,
        group_key='configuration',
        title=key.title(),
        route=f'/{key}',
        order=10,
        layout=lambda _services: None,
        workflow_service=f'{key}.workflow',
        workspace_import_service=f'{key}.import',
        workspace_import_name='Archivo local',
        source_name='SharePoint',
        projection_name='Projection',
        access=ManagerModuleAccess(
            view=access_key,
            validate=access_key,
            publish=access_key,
            project=access_key,
        ),
    )
    registry = ManagerModuleRegistry(
        (ManagerModuleGroup('configuration', 'Configuración', 10),),
        (module,),
    )
    services = ServiceRegistry()
    services.add(module.workflow_service, workflow)
    services.add(module.workspace_import_service, workspace_import)
    principal = ManagerPrincipal(
        subject_id='principal-current',
        display_name='Principal Current',
        access_keys=(access_key,),
    )
    coordinator = ManagerProjectionCoordinator(
        registry=registry,
        services=services,
        authorization=DefaultManagerAuthorizationPolicy(),
    )
    return coordinator, principal


def _seed_store(store, bundle_type, catalog) -> str:
    current = store.fetch_bundle()
    expected = current.revision if current is not None else None
    bundle = bundle_type.create(catalog=catalog, saved_by='Seed Actor')
    store.publish_bundle(bundle, expected_source_revision=expected)
    return bundle.revision


def _build_harness(kind: str, root: Path, *, seed_sharepoint: bool) -> ModuleHarness:
    gateway = MemorySharePointGateway()
    projection = ProjectionProbe()

    if kind == 'tools':
        local_store = FileToolConfigurationStore(
            FileToolConfigurationSettings(root=root / 'local' / 'tools')
        )
        sharepoint_store = SharePointToolConfigurationStore(
            gateway=gateway,
            settings=SharePointToolConfigurationSettings(),
        )
        old_catalog = _tool_catalog('Local Old')
        local_catalog = _tool_catalog('Local Current')
        source_catalog = _tool_catalog('SharePoint Current')
        external_catalog = _tool_catalog('SharePoint External')
        bundle_type = ToolConfigurationBundle
        services = compose_tool_configuration_services(
            source=sharepoint_store,
            publisher=sharepoint_store,
            projection=projection,
            audit_actor_provider=lambda: 'Principal Current',
        )
        workflow = ToolManagerWorkflowAdapter(services)
        workspace_import = ToolWorkspaceImportAdapter(local_store)
    elif kind == 'users':
        local_store = FileUsersConfigurationStore(
            FileUsersConfigurationSettings(root=root / 'local' / 'users')
        )
        sharepoint_store = SharePointUsersConfigurationStore(
            gateway=gateway,
            settings=SharePointUsersConfigurationSettings(),
        )
        old_catalog = _users_catalog('Local Old')
        local_catalog = _users_catalog('Local Current')
        source_catalog = _users_catalog('SharePoint Current')
        external_catalog = _users_catalog('SharePoint External')
        bundle_type = UsersConfigurationBundle
        services = compose_users_configuration_services(
            source=sharepoint_store,
            publisher=sharepoint_store,
            projection=projection,
            discovered=EmptyDiscoveredUsers(),
            audit_actor_provider=lambda: 'Principal Current',
        )
        workflow = UsersManagerWorkflowAdapter(services)
        workspace_import = UsersWorkspaceImportAdapter(local_store)
    elif kind == 'navigation':
        local_store = FileNavigationConfigurationStore(
            FileNavigationConfigurationSettings(root=root / 'local' / 'navigation')
        )
        sharepoint_store = SharePointNavigationConfigurationStore(
            gateway=gateway,
            settings=SharePointNavigationConfigurationSettings(),
        )
        old_catalog = _navigation_catalog('Local Old')
        local_catalog = _navigation_catalog('Local Current')
        source_catalog = _navigation_catalog('SharePoint Current')
        external_catalog = _navigation_catalog('SharePoint External')
        bundle_type = NavigationConfigurationBundle
        services = compose_navigation_configuration_services(
            source=sharepoint_store,
            publisher=sharepoint_store,
            projection=projection,
            audit_actor_provider=lambda: 'Principal Current',
        )
        workflow = NavigationManagerWorkflowAdapter(services)
        workspace_import = NavigationWorkspaceImportAdapter(local_store)
    else:
        raise AssertionError(f'Unsupported module kind: {kind}')

    _seed_store(local_store, bundle_type, old_catalog)
    _seed_store(local_store, bundle_type, local_catalog)
    if seed_sharepoint:
        _seed_store(sharepoint_store, bundle_type, source_catalog)

    coordinator, principal = _manager(
        key=kind,
        workflow=workflow,
        workspace_import=workspace_import,
    )
    return ModuleHarness(
        key=kind,
        local_store=local_store,
        sharepoint_store=sharepoint_store,
        coordinator=coordinator,
        principal=principal,
        projection=projection,
        local_current_document=local_catalog.to_document(),
        external_document=external_catalog.to_document(),
    )


def _publish_external(harness: ModuleHarness) -> str:
    current = harness.sharepoint_store.fetch_bundle()
    assert current is not None
    if harness.key == 'tools':
        bundle = ToolConfigurationBundle.create(
            catalog=ToolConfigurationCatalog.from_document(harness.external_document),
            saved_by='External Principal',
        )
    elif harness.key == 'users':
        bundle = UsersConfigurationBundle.create(
            catalog=UsersConfigurationCatalog.from_document(harness.external_document),
            saved_by='External Principal',
        )
    else:
        bundle = NavigationConfigurationBundle.create(
            catalog=NavigationConfigurationCatalog.from_document(harness.external_document),
            saved_by='External Principal',
        )
    harness.sharepoint_store.publish_bundle(
        bundle,
        expected_source_revision=current.revision,
    )
    return bundle.revision


@pytest.mark.parametrize('kind', ('tools', 'users', 'navigation'))
def test_local_current_promotes_through_manager_to_existing_sharepoint_source(
    tmp_path,
    kind: str,
) -> None:
    harness = _build_harness(kind, tmp_path, seed_sharepoint=True)
    local_history_before = tuple(bundle.revision for bundle in harness.local_store.list_history())
    sharepoint_history_before = tuple(
        bundle.revision for bundle in harness.sharepoint_store.list_history()
    )
    source_before = harness.sharepoint_store.fetch_bundle()
    assert source_before is not None

    imported = harness.coordinator.load_workspace_import(kind, harness.principal)

    assert imported.draft.payload == harness.local_current_document
    assert imported.draft.base_source_revision == source_before.revision
    assert tuple(bundle.revision for bundle in harness.local_store.list_history()) == (
        local_history_before
    )
    assert tuple(bundle.revision for bundle in harness.sharepoint_store.list_history()) == (
        sharepoint_history_before
    )
    assert harness.projection.write_count == 0

    validation = harness.coordinator.validate_draft(
        kind,
        harness.principal,
        imported.draft.payload,
    )
    assert validation.valid
    verification = harness.coordinator.verify_source(
        kind,
        harness.principal,
        draft_revision=imported.draft.revision,
        base_source_revision=imported.draft.base_source_revision,
    )
    assert verification.publishable
    assert not verification.conflict

    publication = harness.coordinator.publish_draft(
        kind,
        harness.principal,
        imported.draft.payload,
        imported.draft.base_source_revision,
    )

    destination = harness.sharepoint_store.fetch_bundle()
    assert destination is not None
    assert destination.revision == publication.source_revision
    assert destination.catalog.to_document() == harness.local_current_document
    assert len(harness.sharepoint_store.list_history()) == len(sharepoint_history_before) + 1
    assert tuple(bundle.revision for bundle in harness.local_store.list_history()) == (
        local_history_before
    )
    assert harness.projection.write_count == 0


@pytest.mark.parametrize('kind', ('tools', 'users', 'navigation'))
def test_local_current_bootstraps_missing_sharepoint_source_without_projection(
    tmp_path,
    kind: str,
) -> None:
    harness = _build_harness(kind, tmp_path, seed_sharepoint=False)
    local_history_before = tuple(bundle.revision for bundle in harness.local_store.list_history())
    assert harness.sharepoint_store.fetch_bundle() is None

    imported = harness.coordinator.load_workspace_import(kind, harness.principal)

    assert imported.draft.base_source_revision is None
    verification = harness.coordinator.verify_source(
        kind,
        harness.principal,
        draft_revision=imported.draft.revision,
        base_source_revision=None,
    )
    assert verification.publishable
    assert not verification.conflict

    harness.coordinator.publish_draft(
        kind,
        harness.principal,
        imported.draft.payload,
        None,
    )

    destination = harness.sharepoint_store.fetch_bundle()
    assert destination is not None
    assert destination.catalog.to_document() == harness.local_current_document
    assert len(harness.sharepoint_store.list_history()) == 1
    assert tuple(bundle.revision for bundle in harness.local_store.list_history()) == (
        local_history_before
    )
    assert harness.projection.write_count == 0


@pytest.mark.parametrize('kind', ('tools', 'users', 'navigation'))
def test_sharepoint_change_after_local_import_is_detected_as_real_conflict(
    tmp_path,
    kind: str,
) -> None:
    harness = _build_harness(kind, tmp_path, seed_sharepoint=True)
    local_history_before = tuple(bundle.revision for bundle in harness.local_store.list_history())
    imported = harness.coordinator.load_workspace_import(kind, harness.principal)
    original_base = imported.draft.base_source_revision
    assert original_base is not None

    external_revision = _publish_external(harness)

    verification = harness.coordinator.verify_source(
        kind,
        harness.principal,
        draft_revision=imported.draft.revision,
        base_source_revision=original_base,
    )
    assert verification.conflict
    assert not verification.publishable
    assert verification.source_revision == external_revision

    with pytest.raises(ManagerSourceConflictError, match='source changed'):
        harness.coordinator.publish_draft(
            kind,
            harness.principal,
            imported.draft.payload,
            original_base,
        )

    destination = harness.sharepoint_store.fetch_bundle()
    assert destination is not None
    assert destination.revision == external_revision
    assert destination.catalog.to_document() == harness.external_document
    assert tuple(bundle.revision for bundle in harness.local_store.list_history()) == (
        local_history_before
    )
    assert harness.projection.write_count == 0
