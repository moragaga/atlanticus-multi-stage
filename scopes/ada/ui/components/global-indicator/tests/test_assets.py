from importlib.resources import files


def test_global_indicator_css_is_packaged_and_ordered() -> None:
    css_root = files('ada.ui.components.global_indicator').joinpath('resources/css')
    entries = css_root.joinpath('css.list').read_text(encoding='utf-8').splitlines()

    assert entries == ['10_global_indicator.css']
    assert css_root.joinpath(entries[0]).is_file()
