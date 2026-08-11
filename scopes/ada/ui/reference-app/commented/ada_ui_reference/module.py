# Espejo comentado de module.py.
from __future__ import annotations

from atlanticus.web.assets import AssetLayer
from atlanticus.web.modules import WebModule


def create_reference_module() -> WebModule:
    return WebModule(
        name='reference',
        page_packages=('ada_ui_reference.pages',),
        asset_layers=(
            AssetLayer(
                name='ada_ui_reference',
                load_order=900,
                package='ada_ui_reference',
            ),
        ),
    )
