from dataclasses import replace

from ada.configuration.tools import (
    ToolConfigurationBundle,
    ToolConfigurationCatalog,
    integrated_operations_configuration_from_manifest,
)
from ada.configuration.tools.adapters.sharepoint import (
    SharePointToolConfigurationSettings,
    SharePointToolConfigurationStore,
)
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST


class FakeSharePointOperation:
    def __init__(self) -> None:
        self.files: dict[tuple[str, str], str] = {}
        self.requests: list[dict[str, object]] = []

    def __call__(self, payload: dict[str, object]) -> dict[str, object]:
        self.requests.append(dict(payload))
        key = (str(payload['relative_path']), str(payload['filename']))
        if 'content' in payload:
            self.files[key] = str(payload['content'])
            return {'ok': True}
        return {'content': self.files.get(key)}


def _catalog() -> ToolConfigurationCatalog:
    return ToolConfigurationCatalog(
        (integrated_operations_configuration_from_manifest(INTEGRATED_OPERATIONS_MANIFEST),)
    )


def test_sharepoint_uses_one_get_post_location_for_current_and_versions() -> None:
    operation = FakeSharePointOperation()
    settings = SharePointToolConfigurationSettings()
    store = SharePointToolConfigurationStore(post_json=operation, settings=settings)
    first = ToolConfigurationBundle.create(catalog=_catalog(), saved_by='Admin A')
    changed = replace(first.catalog.tools[0], display_name='Operaciones Integradas MLP')
    second = ToolConfigurationBundle.create(
        catalog=ToolConfigurationCatalog((changed,)),
        saved_by='Admin B',
    )

    store.publish_bundle(first)
    store.publish_bundle(second)

    expected_key = (settings.relative_path, settings.filename)
    assert set(operation.files) == {expected_key}
    assert [bundle.revision for bundle in store.list_history()] == [
        second.revision,
        first.revision,
    ]
    assert store.fetch_revision(first.revision).catalog == first.catalog
    assert all(request['relative_path'] == settings.relative_path for request in operation.requests)
    assert all(request['filename'] == settings.filename for request in operation.requests)


def test_sharepoint_does_not_duplicate_identical_published_content() -> None:
    operation = FakeSharePointOperation()
    settings = SharePointToolConfigurationSettings()
    store = SharePointToolConfigurationStore(post_json=operation, settings=settings)
    first = ToolConfigurationBundle.create(catalog=_catalog(), saved_by='Admin A')
    same_content = ToolConfigurationBundle.create(catalog=_catalog(), saved_by='Admin B')

    store.publish_bundle(first)
    writes_before = sum('content' in request for request in operation.requests)
    store.publish_bundle(same_content)
    writes_after = sum('content' in request for request in operation.requests)

    assert writes_after == writes_before
    assert store.list_history() == (first,)
