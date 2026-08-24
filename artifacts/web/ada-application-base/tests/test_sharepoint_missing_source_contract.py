import pytest

from atlanticus.web.compositions.sharepoint_http import (
    PowerAutomateSharePointGateway,
    SharePointGatewayError,
)


class FakeHttpStatusError(RuntimeError):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f'HTTP failed with status {status_code}')


class FakeHttpClient:
    def __init__(self, error: Exception) -> None:
        self.error = error

    def request(self, method: str, endpoint: str = '', **kwargs: object) -> object:
        raise self.error

    def request_json(self, method: str, endpoint: str = '', **kwargs: object) -> object:
        raise self.error


def test_installed_sharepoint_gateway_treats_read_404_as_missing_source() -> None:
    gateway = PowerAutomateSharePointGateway(client=FakeHttpClient(FakeHttpStatusError(404)))

    assert gateway.read(filename='users.json.gz', relative_path='configuration/users') is None


def test_installed_sharepoint_gateway_keeps_read_400_as_failure() -> None:
    gateway = PowerAutomateSharePointGateway(client=FakeHttpClient(FakeHttpStatusError(400)))

    with pytest.raises(SharePointGatewayError, match='Power Automate read failed'):
        gateway.read(filename='users.json.gz', relative_path='configuration/users')
