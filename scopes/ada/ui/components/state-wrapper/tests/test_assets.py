from importlib.resources import files


def test_state_wrapper_css_is_packaged() -> None:
    css_root = files('ada.ui.components.state_wrapper').joinpath('resources/css')
    entries = css_root.joinpath('css.list').read_text(encoding='utf-8').splitlines()

    assert entries == ['10-state-wrapper.css']
    assert css_root.joinpath(entries[0]).is_file()


def test_state_overlay_carries_visual_tokens_without_wrapper_parent() -> None:
    css_root = files('ada.ui.components.state_wrapper').joinpath('resources/css')
    css = css_root.joinpath('10-state-wrapper.css').read_text(encoding='utf-8')

    assert '.ada-state-wrapper,\n.ada-state-wrapper__overlay {' in css
    assert '--ada-state-wrapper-overlay-background:' in css
    assert '--ada-state-wrapper-strong-background:' in css
    assert '--ada-state-wrapper-overlay-color:' in css
    assert '--ada-state-wrapper-overlay-message-size:' in css
