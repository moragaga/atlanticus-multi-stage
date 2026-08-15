from importlib.resources import files


def test_process_layout_assets_exist() -> None:
    package = files('ada.ui.layouts.process')
    css_root = package.joinpath('resources/css')

    assert css_root.joinpath('css.list').is_file()
    assert css_root.joinpath('10-process-layout.css').is_file()
