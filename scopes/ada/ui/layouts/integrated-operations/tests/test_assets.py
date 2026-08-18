from importlib.resources import files


def test_integrated_operations_layout_assets_are_body_geometry_only() -> None:
    resources = files('ada.ui.layouts.integrated_operations').joinpath('resources')
    css = resources.joinpath('css')
    css_list = css.joinpath('css.list').read_text().splitlines()

    assert css_list == ['10-integrated-operations-layout.css']
    assert css.joinpath(css_list[0]).is_file()
    assert not resources.joinpath('js').is_dir()


def test_integrated_operations_layout_does_not_own_full_tool_zoom() -> None:
    resources = files('ada.ui.layouts.integrated_operations').joinpath('resources')
    layout_css = resources.joinpath('css', '10-integrated-operations-layout.css').read_text()

    assert 'data-ada-io-view' not in layout_css
    assert 'position: fixed' not in layout_css
    assert '100dvh' not in layout_css
    assert 'ada-io-view' not in layout_css
