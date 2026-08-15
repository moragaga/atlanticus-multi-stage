from importlib.resources import files


def test_integrated_operations_layout_css_is_packaged() -> None:
    resources = files('ada.ui.layouts.integrated_operations').joinpath('resources/css')
    css_list = resources.joinpath('css.list').read_text().splitlines()

    assert css_list == ['10-integrated-operations-layout.css']
    assert resources.joinpath(css_list[0]).is_file()
