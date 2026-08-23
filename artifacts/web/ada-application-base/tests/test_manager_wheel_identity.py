from __future__ import annotations

from importlib.metadata import version
from pathlib import Path
from zipfile import ZipFile

MANAGER_VERSION = '0.3.6'
MANAGER_WHEEL_NAME = f'atlanticus_web_manager-{MANAGER_VERSION}-py3-none-any.whl'


def test_installed_manager_distribution_uses_current_version() -> None:
    assert version('atlanticus-web-manager') == MANAGER_VERSION


def test_manager_transport_has_unique_current_wheel() -> None:
    artifact = Path(__file__).resolve().parents[1]
    wheels = sorted(artifact.joinpath('wheels').glob('atlanticus_web_manager-*.whl'))

    assert [wheel.name for wheel in wheels] == [MANAGER_WHEEL_NAME]


def test_manager_wheel_contains_current_workspace_lifecycle_contract() -> None:
    artifact = Path(__file__).resolve().parents[1]
    wheel = artifact / 'wheels' / MANAGER_WHEEL_NAME

    with ZipFile(wheel) as archive:
        projection = archive.read('atlanticus/web/manager/projection.py').decode('utf-8')
        callbacks = archive.read('atlanticus/web/manager/web/callbacks.py').decode('utf-8')
        layout = archive.read('atlanticus/web/manager/web/layout.py').decode('utf-8')

    assert 'def publishable(self) -> bool:' in projection
    assert "workflow_action_id(MATCH, 'keep-draft')" in callbacks
    assert "f'Usar versión de {module.source_name}'" in layout
    assert "'Mantener mi borrador'" in layout
    assert "Input(workflow_revision_id(MATCH), 'data')" in callbacks
    assert "prevent_initial_call='initial_duplicate'" in callbacks
    assert '_load_current_source_workspace_draft(' in callbacks
    assert "'Descartar cambios locales'" in layout
