from importlib.resources import files


def test_artifact_assets_are_packaged_exactly_once() -> None:
    resources = files('integrated_operations').joinpath('resources', 'css')
    css_list = resources.joinpath('css.list').read_text().splitlines()
    packaged = sorted(
        item.name for item in resources.iterdir() if item.is_file() and item.name != 'css.list'
    )

    assert css_list == ['10-integrated-operations.css']
    assert packaged == css_list
