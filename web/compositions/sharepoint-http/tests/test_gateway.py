import pytest

from atlanticus.web.compositions.sharepoint_http import (
    PowerAutomateSharePointGateway,
    PowerAutomateSharePointSettings,
    SharePointGatewayError,
    SharePointPathSettings,
)


class FakeHttpClient:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.content: str | None = None
        self.response: object | None = None
        self.error: Exception | None = None

    def request(self, method: str, endpoint: str = '', **kwargs: object) -> object:
        self.calls.append({'kind': 'request', 'method': method, 'endpoint': endpoint, **kwargs})
        if self.error is not None:
            raise self.error
        payload = kwargs['json_data']
        assert isinstance(payload, dict)
        self.content = str(payload['content'])
        return object()

    def request_json(self, method: str, endpoint: str = '', **kwargs: object) -> object:
        self.calls.append(
            {'kind': 'request_json', 'method': method, 'endpoint': endpoint, **kwargs}
        )
        if self.error is not None:
            raise self.error
        if self.response is not None:
            return self.response
        return {'success': True, 'content': self.content}


class FakeHttpStatusError(RuntimeError):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f'HTTP failed with status {status_code}')


def test_gateway_uses_independent_read_and_write_endpoints() -> None:
    client = FakeHttpClient()
    gateway = PowerAutomateSharePointGateway(
        client=client,
        settings=PowerAutomateSharePointSettings(
            read_endpoint='read/run',
            write_endpoint='write/run',
            read_parameters={'sig': 'read-secret'},
            write_parameters={'sig': 'write-secret'},
        ),
    )

    assert gateway.read(filename='users.json.gz', relative_path='users') is None
    gateway.write(filename='users.json.gz', relative_path='users', content='encoded')
    assert gateway.read(filename='users.json.gz', relative_path='users') == 'encoded'

    assert [call['method'] for call in client.calls] == ['POST', 'POST', 'POST']
    assert [call['kind'] for call in client.calls] == ['request_json', 'request', 'request_json']
    assert [call['endpoint'] for call in client.calls] == [
        'read/run',
        'write/run',
        'read/run',
    ]
    assert client.calls[0]['params'] == {'sig': 'read-secret'}
    assert client.calls[1]['params'] == {'sig': 'write-secret'}
    assert client.calls[2]['params'] == {'sig': 'read-secret'}
    assert client.calls[0]['json_data'] == {
        'filename': 'users.json.gz',
        'relative_path': 'users',
    }
    assert client.calls[1]['json_data'] == {
        'filename': 'users.json.gz',
        'relative_path': 'users',
        'content': 'encoded',
    }


def test_gateway_rejects_invalid_read_response() -> None:
    client = FakeHttpClient()
    client.response = {'success': True, 'content': 42}
    gateway = PowerAutomateSharePointGateway(client=client)

    with pytest.raises(SharePointGatewayError, match='content must be text'):
        gateway.read(filename='file.json', relative_path='configuration')


def test_gateway_rejects_read_response_that_reports_failure() -> None:
    client = FakeHttpClient()
    client.response = {'success': False, 'content': 'ignored'}
    gateway = PowerAutomateSharePointGateway(client=client)

    with pytest.raises(SharePointGatewayError, match='reported failure'):
        gateway.read(filename='file.json', relative_path='configuration')


def test_gateway_maps_transport_failures_without_exposing_transport_type() -> None:
    client = FakeHttpClient()
    client.error = RuntimeError('transport failed')
    gateway = PowerAutomateSharePointGateway(client=client)

    with pytest.raises(SharePointGatewayError, match='Power Automate write failed'):
        gateway.write(filename='file.json', relative_path='configuration', content='payload')


def test_settings_hide_endpoints_and_parameters_from_repr() -> None:
    settings = PowerAutomateSharePointSettings(
        read_endpoint='read-secret-path',
        write_endpoint='write-secret-path',
        read_parameters={'sig': 'read-secret'},
        write_parameters={'sig': 'write-secret'},
    )

    rendered = repr(settings)
    assert 'read-secret-path' not in rendered
    assert 'write-secret-path' not in rendered
    assert 'read-secret' not in rendered
    assert 'write-secret' not in rendered


def test_path_settings_keep_users_global_and_tool_configuration_scoped() -> None:
    settings = SharePointPathSettings(
        root_path='/conciencia_situacional/',
        tool_path='/operaciones_integradas/',
    )

    assert settings.users_relative_path == 'conciencia_situacional/users'
    assert (
        settings.navigation_relative_path
        == 'conciencia_situacional/operaciones_integradas/navigation'
    )
    assert settings.tool_relative_path == 'conciencia_situacional/operaciones_integradas/tool'
    assert (
        settings.integration_relative_path
        == 'conciencia_situacional/operaciones_integradas/integration'
    )


def test_path_settings_reject_unsafe_relative_paths() -> None:
    with pytest.raises(ValueError, match='safe relative path'):
        SharePointPathSettings(root_path='conciencia_situacional/../other', tool_path='tool')


def test_gateway_maps_read_404_to_missing_file() -> None:
    client = FakeHttpClient()
    client.error = FakeHttpStatusError(404)
    gateway = PowerAutomateSharePointGateway(client=client)

    assert gateway.read(filename='file.json', relative_path='configuration') is None


def test_gateway_keeps_non_404_read_status_as_failure() -> None:
    client = FakeHttpClient()
    error = FakeHttpStatusError(400)
    client.error = error
    gateway = PowerAutomateSharePointGateway(client=client)

    with pytest.raises(SharePointGatewayError, match='Power Automate read failed') as captured:
        gateway.read(filename='file.json', relative_path='configuration')

    assert captured.value.__cause__ is error


def test_gateway_does_not_map_write_404_to_missing_file() -> None:
    client = FakeHttpClient()
    error = FakeHttpStatusError(404)
    client.error = error
    gateway = PowerAutomateSharePointGateway(client=client)

    with pytest.raises(SharePointGatewayError, match='Power Automate write failed') as captured:
        gateway.write(filename='file.json', relative_path='configuration', content='payload')

    assert captured.value.__cause__ is error
