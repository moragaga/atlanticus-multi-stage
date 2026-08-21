from dataclasses import replace

import pytest

from ada.configuration.tools import (
    ToolConfigurationBundle,
    ToolConfigurationCatalog,
    integrated_operations_configuration_from_manifest,
)
from ada.configuration.tools.adapters.sharepoint import (
    SharePointToolConfigurationSettings,
    SharePointToolConfigurationStore,
)
from ada.configuration.tools.errors import ToolConfigurationSourceError
from ada.contracts.tool_manifest import INTEGRATED_OPERATIONS_MANIFEST


class FakeSharePointGateway:
    def __init__(self) -> None:
        self.files: dict[tuple[str, str], str] = {}
        self.reads: list[tuple[str, str]] = []
        self.writes: list[tuple[str, str, str]] = []

    def read(self, *, filename: str, relative_path: str) -> str | None:
        self.reads.append((relative_path, filename))
        return self.files.get((relative_path, filename))

    def write(self, *, filename: str, relative_path: str, content: str) -> None:
        self.writes.append((relative_path, filename, content))
        self.files[(relative_path, filename)] = content


def _catalog() -> ToolConfigurationCatalog:
    return ToolConfigurationCatalog(
        (integrated_operations_configuration_from_manifest(INTEGRATED_OPERATIONS_MANIFEST),)
    )


def test_sharepoint_uses_one_read_write_location_for_current_and_versions() -> None:
    gateway = FakeSharePointGateway()
    settings = SharePointToolConfigurationSettings()
    store = SharePointToolConfigurationStore(gateway=gateway, settings=settings)
    first = ToolConfigurationBundle.create(catalog=_catalog(), saved_by='Admin A')
    changed = replace(first.catalog.tools[0], display_name='Operaciones Integradas MLP')
    second = ToolConfigurationBundle.create(
        catalog=ToolConfigurationCatalog((changed,)),
        saved_by='Admin B',
    )

    store.publish_bundle(first, expected_source_revision=None)
    store.publish_bundle(second, expected_source_revision=first.revision)

    expected_key = (settings.relative_path, settings.filename)
    assert set(gateway.files) == {expected_key}
    assert [bundle.revision for bundle in store.list_history()] == [
        second.revision,
        first.revision,
    ]
    assert store.fetch_revision(first.revision).catalog == first.catalog
    assert all(read == expected_key for read in gateway.reads)
    assert all(write[:2] == expected_key for write in gateway.writes)


def test_sharepoint_does_not_duplicate_identical_published_content() -> None:
    gateway = FakeSharePointGateway()
    settings = SharePointToolConfigurationSettings()
    store = SharePointToolConfigurationStore(gateway=gateway, settings=settings)
    first = ToolConfigurationBundle.create(catalog=_catalog(), saved_by='Admin A')
    same_content = ToolConfigurationBundle.create(catalog=_catalog(), saved_by='Admin B')

    store.publish_bundle(first, expected_source_revision=None)
    writes_before = len(gateway.writes)
    store.publish_bundle(same_content, expected_source_revision=first.revision)
    writes_after = len(gateway.writes)

    assert writes_after == writes_before
    assert store.list_history() == (first,)


def test_sharepoint_rejects_stale_expected_revision_before_write() -> None:
    gateway = FakeSharePointGateway()
    store = SharePointToolConfigurationStore(
        gateway=gateway,
        settings=SharePointToolConfigurationSettings(),
    )
    first = ToolConfigurationBundle.create(catalog=_catalog(), saved_by='Admin A')
    second = ToolConfigurationBundle.create(
        catalog=ToolConfigurationCatalog(
            (replace(first.catalog.tools[0], display_name='Operaciones Integradas MLP'),)
        ),
        saved_by='Admin B',
    )

    store.publish_bundle(first, expected_source_revision=None)
    writes_before = len(gateway.writes)

    with pytest.raises(ToolConfigurationSourceError, match='source revision changed'):
        store.publish_bundle(second, expected_source_revision='stale')

    assert len(gateway.writes) == writes_before
    assert store.fetch_bundle().revision == first.revision
