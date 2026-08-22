from __future__ import annotations

from importlib.metadata import version
from pathlib import Path
from zipfile import ZipFile

TOOLS_VERSION = '0.1.5'
TOOLS_WHEEL_NAME = f'ada_configuration_tools-{TOOLS_VERSION}-py3-none-any.whl'


def test_installed_tools_distribution_uses_current_version() -> None:
    assert version('ada-configuration-tools') == TOOLS_VERSION


def test_tools_transport_has_unique_current_wheel() -> None:
    artifact = Path(__file__).resolve().parents[1]
    wheels = sorted(artifact.joinpath('wheels').glob('ada_configuration_tools-*.whl'))

    assert [wheel.name for wheel in wheels] == [TOOLS_WHEEL_NAME]


def test_tools_wheel_contains_local_duplicate_callback_policy() -> None:
    artifact = Path(__file__).resolve().parents[1]
    wheel = artifact / 'wheels' / TOOLS_WHEEL_NAME

    with ZipFile(wheel) as archive:
        callbacks = archive.read('ada/configuration/tools/web/callbacks.py').decode('utf-8')

    assert "prevent_initial_call='initial_duplicate'" in callbacks
    assert "prevent_initial_callbacks='initial_duplicate'" not in callbacks
