from importlib.resources import files


def test_component_container_css_manifest_matches_packaged_asset() -> None:
    package = files('ada.ui.components.component_container') / 'resources' / 'css'
    listed = (package / 'css.list').read_text(encoding='utf-8').splitlines()

    assert listed == ['10-component-container.css']
    assert (package / '10-component-container.css').is_file()
