from datetime import date

import pytest

from ada.ui.components.branding import (
    ATLANTICUS_BRAND_MANIFEST,
    BrandContext,
    BrandDefinitionError,
    BrandManifest,
    BrandResolutionError,
    BrandVariant,
    MonthDayWindow,
    resolve_brand,
)


def test_atlanticus_manifest_contains_initial_calendar_contract() -> None:
    variants = {variant.key: variant for variant in ATLANTICUS_BRAND_MANIFEST.variants}

    assert tuple(variants) == (
        'fiestas_patrias',
        'halloween',
        'christmas',
        'new_year',
    )
    assert variants['fiestas_patrias'].activation_rule.is_active(date(2026, 9, 30))
    assert variants['halloween'].activation_rule.is_active(date(2026, 10, 25))
    assert variants['christmas'].activation_rule.is_active(date(2026, 12, 1))
    assert variants['new_year'].activation_rule.is_active(date(2027, 1, 2))


def test_auto_resolves_calendar_variant_with_safe_default_asset_fallback() -> None:
    state = resolve_brand(
        ATLANTICUS_BRAND_MANIFEST,
        BrandContext(current_date=date(2026, 9, 18)),
    )

    assert state.variant_key == 'fiestas_patrias'
    assert state.asset_resource == 'atlanticus-primary.png'
    assert state.uses_default_asset is True


def test_default_override_disables_calendar_variant() -> None:
    state = resolve_brand(
        ATLANTICUS_BRAND_MANIFEST,
        BrandContext(current_date=date(2026, 12, 24), requested_variant='default'),
    )

    assert state.variant_key == 'default'
    assert state.asset_resource == 'atlanticus-primary.png'


def test_explicit_variant_can_be_selected_outside_calendar_window() -> None:
    state = resolve_brand(
        ATLANTICUS_BRAND_MANIFEST,
        BrandContext(current_date=date(2026, 8, 12), requested_variant='halloween'),
    )

    assert state.variant_key == 'halloween'
    assert state.uses_default_asset is True


def test_registered_variant_asset_is_used_without_resolver_change() -> None:
    manifest = BrandManifest(
        brand_key='example',
        default_asset_resource='default.png',
        variants=(
            BrandVariant(
                key='special',
                display_name='Special',
                activation_rule=MonthDayWindow(8, 1, 8, 31),
                asset_resource='special.png',
            ),
        ),
    )

    state = resolve_brand(manifest, BrandContext(current_date=date(2026, 8, 12)))

    assert state.variant_key == 'special'
    assert state.asset_resource == 'special.png'
    assert state.uses_default_asset is False


def test_unknown_explicit_variant_is_rejected() -> None:
    with pytest.raises(BrandDefinitionError, match='Unknown brand variant'):
        resolve_brand(
            ATLANTICUS_BRAND_MANIFEST,
            BrandContext(current_date=date(2026, 8, 12), requested_variant='unknown'),
        )


def test_ambiguous_active_variants_are_rejected() -> None:
    manifest = BrandManifest(
        brand_key='example',
        default_asset_resource='default.png',
        variants=(
            BrandVariant('first', 'First', MonthDayWindow(8, 1, 8, 20)),
            BrandVariant('second', 'Second', MonthDayWindow(8, 10, 8, 31)),
        ),
    )

    with pytest.raises(BrandResolutionError, match='Multiple brand variants are active'):
        resolve_brand(manifest, BrandContext(current_date=date(2026, 8, 12)))


def test_reserved_and_duplicate_variant_keys_are_rejected() -> None:
    rule = MonthDayWindow(8, 1, 8, 2)

    with pytest.raises(BrandDefinitionError, match='reserved'):
        BrandManifest(
            brand_key='example',
            default_asset_resource='default.png',
            variants=(BrandVariant('default', 'Default', rule),),
        )

    with pytest.raises(BrandDefinitionError, match='duplicate'):
        BrandManifest(
            brand_key='example',
            default_asset_resource='default.png',
            variants=(
                BrandVariant('special', 'Special', rule),
                BrandVariant('special', 'Special Again', rule),
            ),
        )
