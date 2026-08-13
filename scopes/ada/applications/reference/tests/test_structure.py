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
