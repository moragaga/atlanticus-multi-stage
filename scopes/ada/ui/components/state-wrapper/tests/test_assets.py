from importlib.resources import files


def test_state_wrapper_css_is_packaged() -> None:
    css_root = files('ada.ui.components.state_wrapper').joinpath('resources/css')
    entries = css_root.joinpath('css.list').read_text(encoding='utf-8').splitlines()

    assert entries == ['10_state_wrapper.css']
    assert css_root.joinpath(entries[0]).is_file()
