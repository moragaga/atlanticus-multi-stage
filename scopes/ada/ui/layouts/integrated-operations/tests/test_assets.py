from importlib.resources import files


def test_integrated_operations_layout_assets_are_packaged() -> None:
    resources = files('ada.ui.layouts.integrated_operations').joinpath('resources')
    css = resources.joinpath('css')
    js = resources.joinpath('js')
    css_list = css.joinpath('css.list').read_text().splitlines()
    js_list = js.joinpath('js.list').read_text().splitlines()

    assert css_list == [
        '10-integrated-operations-layout.css',
        '20-integrated-operations-view.css',
    ]
    assert js_list == ['10-integrated-operations-zoom.js']
    assert all(css.joinpath(name).is_file() for name in css_list)
    assert js.joinpath(js_list[0]).is_file()


def test_integrated_operations_zoom_changes_only_full_tool_presentation_state() -> None:
    resources = files('ada.ui.layouts.integrated_operations').joinpath('resources')
    layout_css = resources.joinpath('css', '10-integrated-operations-layout.css').read_text()
    view_css = resources.joinpath('css', '20-integrated-operations-view.css').read_text()
    js = resources.joinpath('js', '10-integrated-operations-zoom.js').read_text()

    assert 'data-ada-io-view' not in layout_css.split('@media (min-width: 96rem)')[0]
    assert 'data-ada-io-view-root="integrated-operations"' in js
    assert "VALID_VIEWS = new Set(['overview', 'mine', 'plant'])" in js
    assert "root.setAttribute('data-ada-io-view', targetView)" in js
    assert 'dcc.Store' not in js
    assert 'fetch(' not in js
    assert "data-ada-io-view='mine'" in view_css
    assert "data-ada-io-view='plant'" in view_css
    assert 'position: fixed;' in view_css
    assert '.ada-io-view__close' in view_css
    assert '.ada-io-view__side--mine' in view_css
    assert '.ada-io-view__side--plant' in view_css
    assert "[data-scope='plant']" in view_css
    assert "[data-scope='mine']" in view_css
