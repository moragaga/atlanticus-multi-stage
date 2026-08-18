from importlib.util import find_spec


def test_legacy_ui_namespaces_are_not_exposed() -> None:
    legacy_names = (
        'ada.ui.branding',
        'ada.ui.core',
        'ada.ui.header',
        'ada.ui.navigation',
        'ada_ui_reference',
    )

    for name in legacy_names:
        assert find_spec(name) is None


def test_feature_ownership_is_not_exposed_under_ui() -> None:
    for name in ('ada.ui.features.alarms', 'ada.ui.features.dashboard'):
        try:
            spec = find_spec(name)
        except ModuleNotFoundError:
            spec = None
        assert spec is None


def test_process_composition_is_exposed_outside_ui_and_features() -> None:
    assert find_spec('ada.compositions.process') is not None


def test_integrated_operations_layout_no_longer_owns_full_tool_view() -> None:
    for name in (
        'ada.ui.layouts.integrated_operations.view',
        'ada.ui.layouts.integrated_operations.models',
    ):
        try:
            spec = find_spec(name)
        except ModuleNotFoundError:
            spec = None
        assert spec is None
