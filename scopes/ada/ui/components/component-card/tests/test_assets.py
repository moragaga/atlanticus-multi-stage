from importlib.resources import files


def test_component_card_css_is_packaged_with_footer_contract() -> None:
    css_root = files('ada.ui.components.component_card').joinpath('resources/css')
    entries = css_root.joinpath('css.list').read_text(encoding='utf-8').splitlines()
    css = css_root.joinpath(entries[0]).read_text(encoding='utf-8')

    assert entries == ['10-component-card.css']
    assert '.ada-component-card__content {' in css
    assert '.ada-component-card__footer {' in css
    assert 'margin-inline-start: auto;' in css
    assert 'padding: .05rem .2rem .08rem;' in css
    assert 'font-size: .65rem;' in css
    assert 'line-height: 1;' in css
