import base64

from atlanticus.web.navigation.configuration import (
    NavigationConfigurationBundle,
    NavigationConfigurationCatalog,
    NavigationLinkConfiguration,
)
from atlanticus.web.navigation.configuration.adapters import (
    SharePointNavigationConfigurationSettings,
    SharePointNavigationConfigurationStore,
)


class FakeSharePointGateway:
    def __init__(self) -> None:
        self.content: str | None = None
        self.reads: list[tuple[str, str]] = []
        self.writes: list[tuple[str, str, str]] = []

    def read(self, *, filename: str, relative_path: str) -> str | None:
        self.reads.append((relative_path, filename))
        return self.content

    def write(self, *, filename: str, relative_path: str, content: str) -> None:
        self.writes.append((relative_path, filename, content))
        self.content = content


def test_sharepoint_store_uses_semantic_read_write_gateway() -> None:
    gateway = FakeSharePointGateway()
    store = SharePointNavigationConfigurationStore(
        gateway=gateway,
        settings=SharePointNavigationConfigurationSettings(),
    )
    bundle = NavigationConfigurationBundle.create(
        catalog=NavigationConfigurationCatalog(
            links=(NavigationLinkConfiguration(key='home', label='Home', href='/'),),
        ),
        saved_by='administrator',
    )

    assert store.fetch_bundle() is None
    store.publish_bundle(bundle)

    assert store.fetch_bundle().revision == bundle.revision
    assert gateway.reads[-1] == ('navigation', 'navigation_configuration.json.gz')
    assert gateway.writes[0][:2] == ('navigation', 'navigation_configuration.json.gz')
    assert base64.b64decode(gateway.writes[0][2], validate=True)
