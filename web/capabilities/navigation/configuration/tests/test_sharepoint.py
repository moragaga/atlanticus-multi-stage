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


def test_sharepoint_store_uses_single_navigation_source_bundle() -> None:
    content: str | None = None
    calls: list[dict[str, object]] = []

    def post_json(payload: dict[str, object]) -> object:
        nonlocal content
        calls.append(payload)
        if 'content' in payload:
            content = str(payload['content'])
            return {'ok': True}
        return {'content': content}

    store = SharePointNavigationConfigurationStore(
        post_json=post_json,
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
    assert calls[-1] == {
        'filename': 'navigation_configuration.json.gz',
        'relative_path': 'navigation',
    }
    assert base64.b64decode(content, validate=True)
