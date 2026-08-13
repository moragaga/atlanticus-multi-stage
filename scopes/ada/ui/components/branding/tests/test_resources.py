from ada.ui.components.branding import brand_asset_package_path, brand_asset_resource


def test_default_asset_is_packaged() -> None:
    resource = brand_asset_resource('atlanticus-primary.png')

    assert resource.is_file()
    assert brand_asset_package_path('atlanticus-primary.png') == (
        'resources/img/atlanticus-primary.png'
    )
