import atlanticus.web.compositions.runtime_infrastructure.runtime as runtime_module
from atlanticus.connectivity.cosmos import CosmosSettings
from atlanticus.connectivity.http import HttpAuthMode, HttpSettings
from atlanticus.web.compositions.runtime_infrastructure import (
    RuntimeInfrastructureError,
    SharePointInfrastructureSettings,
    WebRuntimeInfrastructure,
)
from atlanticus.web.compositions.sharepoint_http import (
    PowerAutomateSharePointSettings,
    SharePointPathSettings,
)


def test_named_cosmos_clients_are_created_once_and_reused() -> None:
    runtime = WebRuntimeInfrastructure(
        cosmos_connections={
            'configuration': _cosmos_settings('ada-configuration'),
            'history': _cosmos_settings('ada-history'),
        }
    )

    assert runtime.cosmos_connection_names == ('configuration', 'history')
    assert runtime.cosmos('configuration') is runtime.cosmos('configuration')
    assert runtime.cosmos('configuration') is not runtime.cosmos('history')


def test_runtime_accepts_arbitrary_solution_connection_names() -> None:
    runtime = WebRuntimeInfrastructure(
        cosmos_connections={
            'tool_projection_store': _cosmos_settings('projection-db'),
        }
    )

    assert runtime.cosmos_connection_names == ('tool_projection_store',)
    assert runtime.cosmos('tool_projection_store').settings.database_name == 'projection-db'


def test_unknown_cosmos_connection_is_rejected() -> None:
    runtime = WebRuntimeInfrastructure(cosmos_connections={'configuration': _cosmos_settings('db')})

    try:
        runtime.cosmos('missing')
    except RuntimeInfrastructureError as error:
        assert str(error) == "Unknown Cosmos connection 'missing'"
    else:
        raise AssertionError('Expected unknown connection to fail')


def test_sharepoint_gateway_and_paths_are_owned_by_runtime() -> None:
    runtime = WebRuntimeInfrastructure(
        cosmos_connections={},
        sharepoint=_sharepoint_settings(),
    )

    assert runtime.sharepoint() is runtime.sharepoint()
    assert runtime.sharepoint_paths.users_relative_path == 'root/users'
    assert runtime.sharepoint_paths.navigation_relative_path == 'root/tool/navigation'


def test_optional_sharepoint_does_not_force_http_resource() -> None:
    runtime = WebRuntimeInfrastructure(cosmos_connections={'configuration': _cosmos_settings('db')})

    try:
        runtime.sharepoint()
    except RuntimeInfrastructureError as error:
        assert str(error) == 'SharePoint infrastructure is not configured'
    else:
        raise AssertionError('Expected missing SharePoint infrastructure to fail')


def test_lifecycle_opens_and_closes_each_owned_client_once(monkeypatch) -> None:
    cosmos_instances = []
    http_instances = []

    class FakeCosmosClient:
        def __init__(self, *, settings):
            self.settings = settings
            self.open_count = 0
            self.close_count = 0
            cosmos_instances.append(self)

        def open(self):
            self.open_count += 1

        def close(self):
            self.close_count += 1

    class FakeHttpClient:
        def __init__(self, *, settings):
            self.settings = settings
            self.open_count = 0
            self.close_count = 0
            http_instances.append(self)

        def open(self):
            self.open_count += 1

        def close(self):
            self.close_count += 1

        def request(self, method, endpoint='', **kwargs):
            del method, endpoint, kwargs

        def request_json(self, method, endpoint='', **kwargs):
            del method, endpoint, kwargs
            return {'success': True, 'content': None}

    monkeypatch.setattr(runtime_module, 'CosmosClient', FakeCosmosClient)
    monkeypatch.setattr(runtime_module, 'HttpClient', FakeHttpClient)

    runtime = WebRuntimeInfrastructure(
        cosmos_connections={
            'configuration': _cosmos_settings('configuration-db'),
            'history': _cosmos_settings('history-db'),
        },
        sharepoint=_sharepoint_settings(),
    )
    runtime.open()
    runtime.open()
    runtime.close()
    runtime.close()

    assert [client.open_count for client in cosmos_instances] == [1, 1]
    assert [client.close_count for client in cosmos_instances] == [1, 1]
    assert len(http_instances) == 1
    assert http_instances[0].open_count == 1
    assert http_instances[0].close_count == 1


def test_failed_open_rolls_back_resources_and_closes_runtime(monkeypatch) -> None:
    instances = []

    class FakeCosmosClient:
        def __init__(self, *, settings):
            self.settings = settings
            self.closed = False
            instances.append(self)

        def open(self):
            if self.settings.database_name == 'broken-db':
                raise RuntimeError('boom')

        def close(self):
            self.closed = True

    monkeypatch.setattr(runtime_module, 'CosmosClient', FakeCosmosClient)
    runtime = WebRuntimeInfrastructure(
        cosmos_connections={
            'configuration': _cosmos_settings('configuration-db'),
            'broken': _cosmos_settings('broken-db'),
        }
    )

    try:
        runtime.open()
    except RuntimeInfrastructureError as error:
        assert str(error) == 'Could not open runtime infrastructure'
    else:
        raise AssertionError('Expected lifecycle startup failure')

    assert instances[0].closed is True
    try:
        runtime.open()
    except RuntimeInfrastructureError as error:
        assert str(error) == 'Runtime infrastructure is closed'
    else:
        raise AssertionError('Expected rolled back runtime to remain closed')


def _cosmos_settings(database_name: str) -> CosmosSettings:
    return CosmosSettings(
        endpoint='https://example.documents.azure.com/',
        key='secret',
        database_name=database_name,
    )


def _sharepoint_settings() -> SharePointInfrastructureSettings:
    return SharePointInfrastructureSettings(
        http=HttpSettings(
            base_url='https://power.example.com/',
            auth_mode=HttpAuthMode.NONE,
        ),
        gateway=PowerAutomateSharePointSettings(
            read_endpoint='/read',
            write_endpoint='/write',
        ),
        paths=SharePointPathSettings(root_path='root', tool_path='tool'),
    )
