from importlib import resources


def test_kpi_admin_css_manifest_is_packaged() -> None:
    root = resources.files('ada.configuration.kpis')
    manifest = root.joinpath('resources/css/css.list')
    css = root.joinpath('resources/css/00_kpis_admin.css')

    assert manifest.is_file()
    assert css.is_file()
    assert manifest.read_text(encoding='utf-8').strip() == '00_kpis_admin.css'
    content = css.read_text(encoding='utf-8')
    assert '.ada-kpis-admin__protected' in content
    assert '.ada-kpis-admin__destination--missing' in content


def test_kpi_admin_asset_layer_has_dedicated_manager_order() -> None:
    module_source = (
        resources.files('ada.configuration.kpis')
        .joinpath('web/module.py')
        .read_text(encoding='utf-8')
    )

    assert 'load_order=720' in module_source
    assert 'load_order=715' not in module_source
