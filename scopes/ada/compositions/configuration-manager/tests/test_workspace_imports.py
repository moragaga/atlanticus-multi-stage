from types import SimpleNamespace

from ada.compositions.configuration_manager.workflows import (
    NavigationWorkspaceImportAdapter,
    ToolWorkspaceImportAdapter,
    UsersWorkspaceImportAdapter,
)


class Catalog:
    def __init__(self, document: dict[str, object]) -> None:
        self._document = document

    def to_document(self) -> dict[str, object]:
        return dict(self._document)


class Source:
    def __init__(self, bundle) -> None:
        self._bundle = bundle
        self.calls = 0

    def fetch_bundle(self):
        self.calls += 1
        return self._bundle


def _assert_adapter(adapter_type) -> None:
    source = Source(
        SimpleNamespace(
            revision='origin-revision',
            catalog=Catalog({'value': 'imported'}),
        )
    )
    adapter = adapter_type(source)

    snapshot = adapter.load_current()

    assert snapshot is not None
    assert snapshot.revision == 'origin-revision'
    assert snapshot.payload == {'value': 'imported'}
    assert source.calls == 1
    assert not hasattr(adapter, 'publish_draft')
    assert not hasattr(adapter, 'project')
    assert not hasattr(adapter, 'list_history')


def test_tool_workspace_import_adapter_is_read_only() -> None:
    _assert_adapter(ToolWorkspaceImportAdapter)


def test_users_workspace_import_adapter_is_read_only() -> None:
    _assert_adapter(UsersWorkspaceImportAdapter)


def test_navigation_workspace_import_adapter_is_read_only() -> None:
    _assert_adapter(NavigationWorkspaceImportAdapter)


def test_workspace_import_adapters_preserve_missing_source() -> None:
    for adapter_type in (
        ToolWorkspaceImportAdapter,
        UsersWorkspaceImportAdapter,
        NavigationWorkspaceImportAdapter,
    ):
        source = Source(None)

        assert adapter_type(source).load_current() is None
        assert source.calls == 1
