from importlib.resources import files


def test_process_base_css_manifest_matches_packaged_assets() -> None:
    resources = files('process_base').joinpath('resources', 'css')
    css_list = resources.joinpath('css.list').read_text().splitlines()
    packaged = sorted(
        item.name for item in resources.iterdir() if item.is_file() and item.name != 'css.list'
    )

    assert css_list == ['10-process-base.css']
    assert packaged == css_list
