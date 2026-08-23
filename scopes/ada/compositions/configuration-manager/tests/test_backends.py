from pathlib import Path

import pytest

import ada.compositions.configuration_manager.backends as backends_module
from ada.compositions.configuration_manager import (
    ConfigurationBackendSelection,
    ConfigurationHistoryBackend,
    ConfigurationImportBackend,
    ConfigurationProjectionBackend,
    create_configuration_manager_dependencies,
    create_configuration_runtime_projection,
    open_configuration_manager_sharepoint_infrastructure,
    resolve_configuration_backend_selection,
)
from ada.compositions.configuration_manager.workflows import (
    NavigationWorkspaceImportAdapter,
    ToolWorkspaceImportAdapter,
    UsersWorkspaceImportAdapter,
)
from ada.compositions.web_bootstrap import AdaConfigurationFilenames, AdaCosmosBindings
from ada.configuration.tools.adapters import (
    FileToolConfigurationStore,
    FileToolProjectionRepository,
    SharePointToolConfigurationStore,
)
from atlanticus.connectivity.cosmos import CosmosSettings
from atlanticus.connectivity.http import HttpAuthMode, HttpSettings
from atlanticus.web.compositions.runtime_infrastructure import (
    SharePointEnvironmentDefinition,
    SharePointInfrastructureSettings,
    WebRuntimeInfrastructure,
)
from atlanticus.web.compositions.sharepoint_http import (
    PowerAutomateSharePointSettings,
    SharePointPathSettings,
)
from atlanticus.web.environment import EnvironmentReader, WebEnvironment
from atlanticus.web.errors import WebConfigurationError
from atlanticus.web.manager import ManagerPrincipal
from atlanticus.web.navigation.configuration import (
    NavigationConfigurationCatalog,
    NavigationLinkConfiguration,
)
from atlanticus.web.navigation.configuration.adapters import (
    FileNavigationConfigurationStore,
    FileNavigationProjectionRepository,
    FileNavigationProjectionSettings,
    SharePointNavigationConfigurationStore,
)
from atlanticus.web.navigation.configuration.projection import (
    NavigationConfigurationProjection,
)
from atlanticus.web.users.configuration import (
    UserProfileConfiguration,
    UsersConfigurationBundle,
    UsersConfigurationCatalog,
)
from atlanticus.web.users.configuration.adapters import (
    FileUsersConfigurationSettings,
    FileUsersConfigurationStore,
    FileUsersProjectionProfileCatalog,
    FileUsersProjectionRepository,
    SharePointUsersConfigurationStore,
)


def _principal() -> ManagerPrincipal:
    return ManagerPrincipal(
        subject_id='local:john-doe',
        display_name='John Doe',
        profile_keys=('local',),
        is_local=True,
    )


def _bindings() -> AdaCosmosBindings:
    return AdaCosmosBindings(
        users='application',
        activity='application',
        navigation='application',
        tools='application',
    )


def _cosmos_infrastructure() -> WebRuntimeInfrastructure:
    return WebRuntimeInfrastructure(
        cosmos_connections={
            'application': CosmosSettings(
                endpoint='https://example.documents.azure.com/',
                key='secret',
                database_name='ada-test',
            )
        }
    )


def _sharepoint_infrastructure() -> WebRuntimeInfrastructure:
    return WebRuntimeInfrastructure(
        cosmos_connections={},
        sharepoint=SharePointInfrastructureSettings(
            http=HttpSettings(
                base_url='https://example.com/',
                auth_mode=HttpAuthMode.NONE,
            ),
            gateway=PowerAutomateSharePointSettings(),
            paths=SharePointPathSettings(
                root_path='configuration',
                tool_path='ada',
            ),
        ),
    )


def test_local_defaults_to_file_history_and_file_projection() -> None:
    selection = resolve_configuration_backend_selection(
        EnvironmentReader({}),
        WebEnvironment.LOCAL,
    )

    assert selection == ConfigurationBackendSelection(
        history=ConfigurationHistoryBackend.LOCAL,
        projection=ConfigurationProjectionBackend.LOCAL,
    )
    assert selection.requires_sharepoint is False


def test_local_supports_file_to_cosmos_and_sharepoint_to_cosmos() -> None:
    file_to_cosmos = resolve_configuration_backend_selection(
        EnvironmentReader(
            {
                'ATLANTICUS_CONFIGURATION_HISTORY_BACKEND': 'local',
                'ATLANTICUS_CONFIGURATION_PROJECTION_BACKEND': 'cosmos',
            }
        ),
        WebEnvironment.LOCAL,
    )
    sharepoint_to_cosmos = resolve_configuration_backend_selection(
        EnvironmentReader(
            {
                'ATLANTICUS_CONFIGURATION_HISTORY_BACKEND': 'sharepoint',
                'ATLANTICUS_CONFIGURATION_PROJECTION_BACKEND': 'cosmos',
            }
        ),
        WebEnvironment.LOCAL,
    )

    assert file_to_cosmos == ConfigurationBackendSelection(
        history=ConfigurationHistoryBackend.LOCAL,
        projection=ConfigurationProjectionBackend.COSMOS,
    )
    assert sharepoint_to_cosmos == ConfigurationBackendSelection(
        history=ConfigurationHistoryBackend.SHAREPOINT,
        projection=ConfigurationProjectionBackend.COSMOS,
    )
    assert sharepoint_to_cosmos.requires_sharepoint is True


def test_local_rejects_sharepoint_history_with_file_projection() -> None:
    with pytest.raises(WebConfigurationError, match='requires Cosmos projection'):
        resolve_configuration_backend_selection(
            EnvironmentReader(
                {
                    'ATLANTICUS_CONFIGURATION_HISTORY_BACKEND': 'sharepoint',
                    'ATLANTICUS_CONFIGURATION_PROJECTION_BACKEND': 'local',
                }
            ),
            WebEnvironment.LOCAL,
        )


def test_production_forces_sharepoint_history_and_cosmos_projection() -> None:
    selection = resolve_configuration_backend_selection(
        EnvironmentReader({}),
        WebEnvironment.PRODUCTION,
    )

    assert selection == ConfigurationBackendSelection(
        history=ConfigurationHistoryBackend.SHAREPOINT,
        projection=ConfigurationProjectionBackend.COSMOS,
    )
    assert selection.requires_sharepoint is True

    with pytest.raises(WebConfigurationError, match='history is only supported'):
        resolve_configuration_backend_selection(
            EnvironmentReader({'ATLANTICUS_CONFIGURATION_HISTORY_BACKEND': 'local'}),
            WebEnvironment.PRODUCTION,
        )
    with pytest.raises(WebConfigurationError, match='projection is only supported'):
        resolve_configuration_backend_selection(
            EnvironmentReader({'ATLANTICUS_CONFIGURATION_PROJECTION_BACKEND': 'local'}),
            WebEnvironment.PRODUCTION,
        )


def test_workspace_import_backend_is_optional_and_orthogonal_to_environment() -> None:
    local_default = resolve_configuration_backend_selection(
        EnvironmentReader({}),
        WebEnvironment.LOCAL,
    )
    local_import = resolve_configuration_backend_selection(
        EnvironmentReader({'ATLANTICUS_CONFIGURATION_IMPORT_BACKEND': 'local'}),
        WebEnvironment.LOCAL,
    )
    production_import = resolve_configuration_backend_selection(
        EnvironmentReader({'ATLANTICUS_CONFIGURATION_IMPORT_BACKEND': 'local'}),
        WebEnvironment.PRODUCTION,
    )

    assert local_default.workspace_import is ConfigurationImportBackend.NONE
    assert local_import.workspace_import is ConfigurationImportBackend.LOCAL
    assert production_import.workspace_import is ConfigurationImportBackend.LOCAL
    assert production_import.history is ConfigurationHistoryBackend.SHAREPOINT
    assert production_import.projection is ConfigurationProjectionBackend.COSMOS

    with pytest.raises(WebConfigurationError, match='ATLANTICUS_CONFIGURATION_IMPORT_BACKEND'):
        resolve_configuration_backend_selection(
            EnvironmentReader({'ATLANTICUS_CONFIGURATION_IMPORT_BACKEND': 'sharepoint'}),
            WebEnvironment.LOCAL,
        )


def test_sharepoint_infrastructure_opens_only_when_history_requires_it(monkeypatch) -> None:
    events = []
    resolved_settings = object()

    class FakeInfrastructure:
        def __init__(self, *, cosmos_connections, sharepoint=None):
            events.append(('created', cosmos_connections, sharepoint))

        def open(self):
            events.append('open')

    monkeypatch.setattr(backends_module, 'WebRuntimeInfrastructure', FakeInfrastructure)
    monkeypatch.setattr(
        backends_module,
        'resolve_sharepoint_infrastructure_settings',
        lambda environment, definition: (
            events.append(('resolved', environment, definition)) or resolved_settings
        ),
    )
    definition = SharePointEnvironmentDefinition(
        read_endpoint_variable='SP_READ',
        write_endpoint_variable='SP_WRITE',
        root_path_variable='SP_ROOT',
        tool_path_variable='SP_TOOL',
    )
    reader = EnvironmentReader({})

    local_result = open_configuration_manager_sharepoint_infrastructure(
        selection=ConfigurationBackendSelection(
            history=ConfigurationHistoryBackend.LOCAL,
            projection=ConfigurationProjectionBackend.LOCAL,
        ),
        environment=reader,
        definition=definition,
    )
    sharepoint_result = open_configuration_manager_sharepoint_infrastructure(
        selection=ConfigurationBackendSelection(
            history=ConfigurationHistoryBackend.SHAREPOINT,
            projection=ConfigurationProjectionBackend.COSMOS,
        ),
        environment=reader,
        definition=definition,
    )

    assert local_result is None
    assert isinstance(sharepoint_result, FakeInfrastructure)
    assert events == [
        ('resolved', reader, definition),
        ('created', {}, resolved_settings),
        'open',
    ]


def test_local_runtime_projection_reads_file_profiles_and_navigation(tmp_path) -> None:
    selection = ConfigurationBackendSelection(
        history=ConfigurationHistoryBackend.LOCAL,
        projection=ConfigurationProjectionBackend.LOCAL,
    )
    runtime_projection = create_configuration_runtime_projection(
        selection=selection,
        runtime_root=tmp_path,
    )

    assert runtime_projection is not None
    assert isinstance(runtime_projection.profiles, FileUsersProjectionProfileCatalog)
    assert runtime_projection.profiles._repository._settings.root == (
        tmp_path / 'projection' / 'users'
    )
    assert runtime_projection.navigation_provider.current().links == ()

    users_repository = FileUsersProjectionRepository(
        FileUsersConfigurationSettings(root=tmp_path / 'projection' / 'users')
    )
    users_repository.project(
        UsersConfigurationBundle.create(
            catalog=UsersConfigurationCatalog(
                profiles=(
                    UserProfileConfiguration(
                        key='operator',
                        label='Operador',
                        background_color='#445566',
                    ),
                )
            ),
            saved_by='John Doe',
        ),
        actor='John Doe',
    )

    assert runtime_projection.profiles.require('operator').label == 'Operador'

    repository = FileNavigationProjectionRepository(
        FileNavigationProjectionSettings(root=tmp_path / 'projection' / 'navigation')
    )
    repository.save(
        NavigationConfigurationProjection.create(
            source_revision='navigation-source',
            projected_by='John Doe',
            catalog=NavigationConfigurationCatalog(
                links=(NavigationLinkConfiguration(key='home', label='Inicio', href='/'),)
            ),
        )
    )

    assert runtime_projection.navigation_provider.current().links[0].key == 'home'


def test_cosmos_runtime_projection_uses_existing_bootstrap_path() -> None:
    runtime_projection = create_configuration_runtime_projection(
        selection=ConfigurationBackendSelection(
            history=ConfigurationHistoryBackend.LOCAL,
            projection=ConfigurationProjectionBackend.COSMOS,
        )
    )

    assert runtime_projection is None


def test_local_file_dependencies_keep_history_and_projection_in_separate_roots(tmp_path) -> None:
    dependencies = create_configuration_manager_dependencies(
        selection=ConfigurationBackendSelection(
            history=ConfigurationHistoryBackend.LOCAL,
            projection=ConfigurationProjectionBackend.LOCAL,
        ),
        infrastructure=WebRuntimeInfrastructure(cosmos_connections={}),
        bindings=_bindings(),
        filenames=AdaConfigurationFilenames(),
        principal_provider=_principal,
        runtime_root=tmp_path,
    )

    assert isinstance(dependencies.tools.administration._source, FileToolConfigurationStore)
    assert isinstance(dependencies.tools.projection, FileToolProjectionRepository)
    assert isinstance(dependencies.users.administration._source, FileUsersConfigurationStore)
    assert isinstance(dependencies.users.projection, FileUsersProjectionRepository)
    assert isinstance(
        dependencies.navigation.administration._source,
        FileNavigationConfigurationStore,
    )
    assert isinstance(dependencies.navigation.projection, FileNavigationProjectionRepository)
    assert dependencies.tools_source_name == 'Archivo local'
    assert dependencies.tools_projection_name == 'Archivo local'

    roots = {
        dependencies.tools.administration._source._settings.root,
        dependencies.users.administration._source._settings.root,
        dependencies.navigation.administration._source._settings.root,
    }
    assert roots == {
        Path(tmp_path) / 'source' / 'tools',
        Path(tmp_path) / 'source' / 'users',
        Path(tmp_path) / 'source' / 'navigation',
    }
    projection_roots = {
        dependencies.tools.projection._settings.root,
        dependencies.users.projection._settings.root,
        dependencies.navigation.projection._settings.root,
    }
    assert projection_roots == {
        Path(tmp_path) / 'projection' / 'tools',
        Path(tmp_path) / 'projection' / 'users',
        Path(tmp_path) / 'projection' / 'navigation',
    }


def test_local_file_history_can_project_to_cosmos_without_sharepoint(tmp_path) -> None:
    dependencies = create_configuration_manager_dependencies(
        selection=ConfigurationBackendSelection(
            history=ConfigurationHistoryBackend.LOCAL,
            projection=ConfigurationProjectionBackend.COSMOS,
        ),
        infrastructure=_cosmos_infrastructure(),
        bindings=_bindings(),
        filenames=AdaConfigurationFilenames(),
        principal_provider=_principal,
        runtime_root=tmp_path,
    )

    assert isinstance(dependencies.tools.administration._source, FileToolConfigurationStore)
    assert dependencies.tools_source_name == 'Archivo local'
    assert dependencies.tools_projection_name == 'Cosmos DB'
    assert dependencies.users_projection_name == 'Cosmos DB'
    assert dependencies.navigation_projection_name == 'Cosmos DB'


def test_sharepoint_history_uses_separate_history_infrastructure_and_cosmos_projection() -> None:
    dependencies = create_configuration_manager_dependencies(
        selection=ConfigurationBackendSelection(
            history=ConfigurationHistoryBackend.SHAREPOINT,
            projection=ConfigurationProjectionBackend.COSMOS,
        ),
        infrastructure=_cosmos_infrastructure(),
        sharepoint_infrastructure=_sharepoint_infrastructure(),
        bindings=_bindings(),
        filenames=AdaConfigurationFilenames(),
        principal_provider=_principal,
    )

    assert isinstance(dependencies.tools.administration._source, SharePointToolConfigurationStore)
    assert isinstance(dependencies.users.administration._source, SharePointUsersConfigurationStore)
    assert isinstance(
        dependencies.navigation.administration._source,
        SharePointNavigationConfigurationStore,
    )
    assert dependencies.tools_source_name == 'SharePoint'
    assert dependencies.users_source_name == 'SharePoint'
    assert dependencies.navigation_source_name == 'SharePoint'
    assert dependencies.tools_projection_name == 'Cosmos DB'
    assert dependencies.users_projection_name == 'Cosmos DB'
    assert dependencies.navigation_projection_name == 'Cosmos DB'
    assert dependencies.force_publish_enabled is False


def test_sharepoint_history_can_enable_force_publication_explicitly() -> None:
    dependencies = create_configuration_manager_dependencies(
        selection=ConfigurationBackendSelection(
            history=ConfigurationHistoryBackend.SHAREPOINT,
            projection=ConfigurationProjectionBackend.COSMOS,
        ),
        infrastructure=_cosmos_infrastructure(),
        sharepoint_infrastructure=_sharepoint_infrastructure(),
        bindings=_bindings(),
        filenames=AdaConfigurationFilenames(),
        principal_provider=_principal,
        force_publish_enabled=True,
        web_environment=WebEnvironment.PRODUCTION,
    )

    assert dependencies.force_publish_enabled is True


def test_force_publication_rejects_local_environment() -> None:
    selection = ConfigurationBackendSelection(
        history=ConfigurationHistoryBackend.SHAREPOINT,
        projection=ConfigurationProjectionBackend.COSMOS,
    )

    with pytest.raises(WebConfigurationError, match='only supported in production'):
        create_configuration_manager_dependencies(
            selection=selection,
            infrastructure=_cosmos_infrastructure(),
            sharepoint_infrastructure=_sharepoint_infrastructure(),
            bindings=_bindings(),
            filenames=AdaConfigurationFilenames(),
            principal_provider=_principal,
            force_publish_enabled=True,
            web_environment=WebEnvironment.LOCAL,
        )


def test_force_publication_rejects_local_history() -> None:
    with pytest.raises(WebConfigurationError, match='requires SharePoint'):
        create_configuration_manager_dependencies(
            selection=ConfigurationBackendSelection(
                history=ConfigurationHistoryBackend.LOCAL,
                projection=ConfigurationProjectionBackend.LOCAL,
            ),
            infrastructure=WebRuntimeInfrastructure(cosmos_connections={}),
            bindings=_bindings(),
            filenames=AdaConfigurationFilenames(),
            principal_provider=_principal,
            force_publish_enabled=True,
        )


def test_sharepoint_history_requires_dedicated_sharepoint_infrastructure() -> None:
    with pytest.raises(WebConfigurationError, match='requires SharePoint infrastructure'):
        create_configuration_manager_dependencies(
            selection=ConfigurationBackendSelection(
                history=ConfigurationHistoryBackend.SHAREPOINT,
                projection=ConfigurationProjectionBackend.COSMOS,
            ),
            infrastructure=_cosmos_infrastructure(),
            bindings=_bindings(),
            filenames=AdaConfigurationFilenames(),
            principal_provider=_principal,
        )


def test_sharepoint_source_can_wire_local_workspace_import_independently(tmp_path) -> None:
    dependencies = create_configuration_manager_dependencies(
        selection=ConfigurationBackendSelection(
            history=ConfigurationHistoryBackend.SHAREPOINT,
            projection=ConfigurationProjectionBackend.COSMOS,
            workspace_import=ConfigurationImportBackend.LOCAL,
        ),
        infrastructure=_cosmos_infrastructure(),
        sharepoint_infrastructure=_sharepoint_infrastructure(),
        bindings=_bindings(),
        filenames=AdaConfigurationFilenames(),
        principal_provider=_principal,
        runtime_root=tmp_path,
    )

    assert isinstance(dependencies.tools.administration._source, SharePointToolConfigurationStore)
    assert isinstance(dependencies.users.administration._source, SharePointUsersConfigurationStore)
    assert isinstance(
        dependencies.navigation.administration._source,
        SharePointNavigationConfigurationStore,
    )
    assert isinstance(dependencies.tools_workspace_import, ToolWorkspaceImportAdapter)
    assert isinstance(dependencies.users_workspace_import, UsersWorkspaceImportAdapter)
    assert isinstance(dependencies.navigation_workspace_import, NavigationWorkspaceImportAdapter)
    assert dependencies.tools_workspace_import_name == 'Archivo local'
    assert dependencies.users_workspace_import_name == 'Archivo local'
    assert dependencies.navigation_workspace_import_name == 'Archivo local'
    assert (
        dependencies.tools_workspace_import._source._settings.root == tmp_path / 'source' / 'tools'
    )
    assert (
        dependencies.users_workspace_import._source._settings.root == tmp_path / 'source' / 'users'
    )
    assert (
        dependencies.navigation_workspace_import._source._settings.root
        == tmp_path / 'source' / 'navigation'
    )


def test_workspace_import_is_not_wired_when_backend_is_none(tmp_path) -> None:
    dependencies = create_configuration_manager_dependencies(
        selection=ConfigurationBackendSelection(
            history=ConfigurationHistoryBackend.LOCAL,
            projection=ConfigurationProjectionBackend.LOCAL,
        ),
        infrastructure=WebRuntimeInfrastructure(cosmos_connections={}),
        bindings=_bindings(),
        filenames=AdaConfigurationFilenames(),
        principal_provider=_principal,
        runtime_root=tmp_path,
    )

    assert dependencies.tools_workspace_import is None
    assert dependencies.users_workspace_import is None
    assert dependencies.navigation_workspace_import is None
    assert dependencies.tools_workspace_import_name is None
    assert dependencies.users_workspace_import_name is None
    assert dependencies.navigation_workspace_import_name is None
