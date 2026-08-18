from importlib.resources import files


def test_integrated_operations_composition_assets_are_packaged_exactly_once() -> None:
    resources = files('ada.compositions.integrated_operations').joinpath('resources', 'css')
    css_list = resources.joinpath('css.list').read_text().splitlines()
    packaged = sorted(
        item.name for item in resources.iterdir() if item.is_file() and item.name != 'css.list'
    )

    assert css_list == ['10-integrated-operations-composition.css']
    assert packaged == css_list


def test_alarm_baseline_is_edge_to_edge_and_body_keeps_its_own_padding() -> None:
    resources = files('ada.compositions.integrated_operations').joinpath('resources', 'css')
    css = resources.joinpath('10-integrated-operations-composition.css').read_text()

    assert '.ada-integrated-operations-tool__alarm-surface {' in css
    assert 'padding: 0;' in css
    assert '.ada-integrated-operations-tool__alarm-content {' in css
    assert 'padding-inline: var(--ada-integrated-operations-tool-gap);' in css
    assert '--ada-alarm-scope-split: 44.444444%;' in css
