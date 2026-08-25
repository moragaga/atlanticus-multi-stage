from importlib.resources import files


def test_operational_shell_css_manifest_references_existing_asset() -> None:
    root = files('ada.ui.shell.operational').joinpath('resources/css')
    manifest = root.joinpath('css.list').read_text(encoding='utf-8').splitlines()

    assert manifest == ['10-operational-shell.css']
    assert root.joinpath(manifest[0]).is_file()
