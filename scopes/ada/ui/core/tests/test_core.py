from pathlib import Path

from ada.ui.core import ADA_UI_ASSET_LAYER, create_ada_ui_module


def test_ada_ui_core_declares_foundational_assets_only() -> None:
    module = create_ada_ui_module()

    assert module.name == 'ada-ui'
    assert module.asset_layers == (ADA_UI_ASSET_LAYER,)
    assert ADA_UI_ASSET_LAYER.load_order == 100
    assert module.register_callbacks is None
    assert module.register_routes is None


def test_ada_ui_core_preserves_approved_bootstrap_and_tokens() -> None:
    resources = Path(__file__).parents[1] / 'src' / 'ada' / 'ui' / 'core' / 'resources'
    bootstrap = (resources / 'css' / '00_bootstrap.min.css').read_text(encoding='utf-8')
    tokens = (resources / 'css' / '10_tokens.css').read_text(encoding='utf-8')

    assert 'Bootstrap  v5.3.3' in bootstrap
    assert '--primary-background: #EBEBEB;' in tokens
    assert '--loader-color: #2E2E2E;' in tokens
    assert '--dark-color: #313131;' in tokens
