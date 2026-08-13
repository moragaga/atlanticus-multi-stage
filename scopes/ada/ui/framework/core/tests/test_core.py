from pathlib import Path

import pytest

from ada.ui.framework.core import (
    ADA_UI_ASSET_LAYER,
    DisplayStatus,
    DisplayValue,
    build_ready_scope,
    coerce_display_value,
    create_ada_ui_module,
    ready_attributes,
    resolve_status_visual,
)


def test_ada_ui_framework_core_declares_foundational_assets_only() -> None:
    module = create_ada_ui_module()

    assert module.name == 'ada-ui'
    assert module.asset_layers == (ADA_UI_ASSET_LAYER,)
    assert ADA_UI_ASSET_LAYER.load_order == 100
    assert module.register_callbacks is None
    assert module.register_routes is None


def test_ada_ui_framework_core_preserves_approved_bootstrap_and_tokens() -> None:
    resources = (
        Path(__file__).parents[1]
        / 'src'
        / 'ada'
        / 'ui'
        / 'framework'
        / 'core'
        / 'resources'
    )
    bootstrap = (resources / 'css' / '00-bootstrap.min.css').read_text(encoding='utf-8')
    tokens = (resources / 'css' / '10-tokens.css').read_text(encoding='utf-8')

    assert 'Bootstrap  v5.3.3' in bootstrap
    assert '--primary-background: #EBEBEB;' in tokens
    assert '--loader-color: #2E2E2E;' in tokens
    assert '--dark-color: #313131;' in tokens


def test_status_visuals_use_approved_kebab_case_assets() -> None:
    resources = (
        Path(__file__).parents[1]
        / 'src'
        / 'ada'
        / 'ui'
        / 'framework'
        / 'core'
        / 'resources'
    )
    expected = {
        'not-mapped.svg',
        'invalid-data.svg',
        'empty-data.svg',
        'internal-error.svg',
    }

    assert {path.name for path in (resources / 'img' / 'status').glob('*.svg')} == expected
    visual = resolve_status_visual(DisplayStatus.INVALID)
    assert visual is not None
    assert visual.asset_name == 'invalid-data.svg'
    assert '/img/status/invalid-data.svg' in visual.asset_url


def test_display_value_coercion_is_defensive() -> None:
    assert coerce_display_value(None).status is DisplayStatus.EMPTY
    assert coerce_display_value('42') == DisplayValue.ok('42')
    assert coerce_display_value(None, present=False).status is DisplayStatus.NOT_MAPPED
    invalid = coerce_display_value({'status': 'invalid', 'value': 'bad'})
    assert invalid.status is DisplayStatus.INVALID
    assert coerce_display_value({'status': 'unknown'}).status is DisplayStatus.ERROR


def test_ready_scope_requires_named_components() -> None:
    component = build_ready_scope(
        content=[],
        required=('header', 'page-content'),
    )
    props = component.to_plotly_json()['props']

    assert props['data-ready-state'] == 'loading'
    assert props['data-ready-required'] == 'header,page-content'
    assert ready_attributes('header', ready=True)['data-ready'] == 'true'

    with pytest.raises(ValueError, match='duplicate'):
        build_ready_scope(content=[], required=('header', 'header'))


def test_status_icons_use_shared_rem_tokens_and_scalable_svg_canvas() -> None:
    resources = (
        Path(__file__).parents[1]
        / 'src'
        / 'ada'
        / 'ui'
        / 'framework'
        / 'core'
        / 'resources'
    )
    tokens = (resources / 'css' / '10-tokens.css').read_text(encoding='utf-8')
    status_css = (resources / 'css' / '20-status.css').read_text(encoding='utf-8')

    assert '--ada-status-icon-size: 1rem;' in tokens
    assert '--ada-cover-icon-box-size: 1.5rem;' in tokens
    assert '--ada-cover-icon-size: 1.25rem;' in tokens
    assert 'var(--ada-status-icon-size)' in status_css

    for asset in (resources / 'img' / 'status').glob('*.svg'):
        svg = asset.read_text(encoding='utf-8')
        assert 'viewBox=' in svg
        assert ' width=' not in svg
        assert ' height=' not in svg

    internal_error = (resources / 'img' / 'status' / 'internal-error.svg').read_text(
        encoding='utf-8'
    )
    assert 'viewBox="0 0 16 16"' in internal_error
