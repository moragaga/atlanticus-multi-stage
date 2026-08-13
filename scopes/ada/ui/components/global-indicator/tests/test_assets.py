from importlib.resources import files


def test_global_indicator_css_is_packaged_and_preserves_equal_size_contract() -> None:
    css_root = files('ada.ui.components.global_indicator').joinpath('resources/css')
    entries = css_root.joinpath('css.list').read_text(encoding='utf-8').splitlines()
    css = css_root.joinpath(entries[0]).read_text(encoding='utf-8')

    assert entries == ['10_global_indicator.css']
    assert 'flex: 1 1 0;' in css
    assert 'min-width: 0;' in css
    assert 'min-height: 5.5rem;' in css
