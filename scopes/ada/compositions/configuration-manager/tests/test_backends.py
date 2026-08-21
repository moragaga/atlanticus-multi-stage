from pathlib import Path

import pytest

import ada.compositions.configuration_manager.backends as backends_module
from ada.compositions.configuration_manager import (
    ConfigurationBackendSelection,
    ConfigurationHistoryBackend,
    ConfigurationProjectionBackend,
    create_configuration_manager_dependencies,
    open_configuration_manager_sharepoint_infrastructure,
    resolve_configuration_backend_selection,
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
from atlanticus.web.navigation.configuration.adapters import (
    FileNavigationConfigurationStore,
    FileNavigationProjectionRepository,
    SharePointNavigationConfigurationStore,
)
from atlanticus.web.users.configuration.adapters import (
    FileUsersConfigurationStore,
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
