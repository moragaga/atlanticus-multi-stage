from importlib.resources import files


def test_integrated_operations_composition_assets_are_packaged_exactly_once() -> None:
    resources = files('ada.compositions.integrated_operations').joinpath('resources')

    css_resources = resources.joinpath('css')
    css_list = css_resources.joinpath('css.list').read_text().splitlines()
    packaged_css = sorted(
        item.name for item in css_resources.iterdir() if item.is_file() and item.name != 'css.list'
    )
    assert css_list == ['10-integrated-operations-composition.css']
    assert packaged_css == css_list

    js_resources = resources.joinpath('js')
    js_list = js_resources.joinpath('js.list').read_text().splitlines()
    packaged_js = sorted(
        item.name for item in js_resources.iterdir() if item.is_file() and item.name != 'js.list'
    )
    assert js_list == ['10-integrated-operations-presentation.js']
    assert packaged_js == js_list


def test_integrated_operations_zoom_keeps_alarm_and_body_geometry_stable() -> None:
    resources = files('ada.compositions.integrated_operations').joinpath('resources')
    css = resources.joinpath('css', '10-integrated-operations-composition.css').read_text()
    js = resources.joinpath('js', '10-integrated-operations-presentation.js').read_text()

    assert '--ada-integrated-operations-alarm-content-size: 5rem;' in css
    assert '--ada-integrated-operations-alarm-surface-size:' in css
    assert "[data-ada-io-presentation='mine']" in css
    assert 'width: 225%;' in css
    assert 'width: 180%;' in css
    assert 'translateX(-44.444444%)' in css
    assert 'visibility: hidden;' not in css
    assert ".ada-alarm-management-summary__segment[data-scope='plant']" in css
    assert ".ada-alarm-management-summary__segment[data-scope='mine']" in css
    assert 'flex: 0 0 calc(100% / var(--ada-io-overview-indicator-count));' in css
    assert '.ada-alarm-dashboard-baseline__scope-divider' in css
    assert 'column-gap: var(--ada-integrated-operations-tool-gap);' in css
    assert '.ada-integrated-operations-tool .ada-header__management-slot' in css
    assert 'border-left: 1px solid var(--ada-header-border' in css
    assert '> .ada-header__global-indicator:last-child' in css
    assert 'border-right: 0;' in css
    assert '.ada-io-layout__scope--plant {\n        display: none;' not in css
    assert '.ada-io-layout__scope--mine {\n        display: none;' not in css
    assert "const VALID_PRESENTATIONS = new Set(['overview', 'mine', 'plant']);" in js
    assert "'ada:alarm-geometry-refresh'" in js
