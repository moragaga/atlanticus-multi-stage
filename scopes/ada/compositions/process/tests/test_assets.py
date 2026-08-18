from importlib.resources import files


def test_process_composition_assets_are_packaged() -> None:
    resources = files('ada.compositions.process').joinpath('resources', 'css')
    css_list = resources.joinpath('css.list').read_text().splitlines()
    packaged = sorted(
        item.name for item in resources.iterdir() if item.is_file() and item.name != 'css.list'
    )

    assert css_list == ['10-process-composition.css']
    assert packaged == css_list
    css = resources.joinpath(css_list[0]).read_text()
    assert '.ada-process-tool__body' in css
    assert '--ada-process-tool-surface:' in css
    assert '--ada-process-tool-bottom-size:' in css
    assert 'background: var(--ada-process-tool-surface);' in css
    assert '.ada-process-tool__alarm-surface' in css
    assert 'overflow: visible;' in css
    assert 'overflow: hidden;' in css
    assert '.ada-process-tool__component-cards' in css
    assert '--ada-component-card-background: var(--ada-process-tool-card-surface);' in css
    assert 'flex: 1 1 auto;' in css
