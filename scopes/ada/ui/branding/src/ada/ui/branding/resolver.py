from __future__ import annotations

from .errors import BrandResolutionError
from .models import BrandContext, BrandManifest, BrandState, BrandVariant


def resolve_brand(manifest: BrandManifest, context: BrandContext) -> BrandState:
    if context.requested_variant == 'default':
        return _default_state(manifest)

    if context.requested_variant != 'auto':
        return _variant_state(manifest, manifest.variant(context.requested_variant))

    active = tuple(
        variant
        for variant in manifest.variants
        if variant.activation_rule.is_active(context.current_date)
    )
    if not active:
        return _default_state(manifest)
    if len(active) > 1:
        keys = ', '.join(variant.key for variant in active)
        raise BrandResolutionError(f'Multiple brand variants are active: {keys}')
    return _variant_state(manifest, active[0])


def _default_state(manifest: BrandManifest) -> BrandState:
    return BrandState(
        brand_key=manifest.brand_key,
        variant_key='default',
        asset_resource=manifest.default_asset_resource,
        uses_default_asset=True,
    )


def _variant_state(manifest: BrandManifest, variant: BrandVariant) -> BrandState:
    asset_resource = variant.asset_resource or manifest.default_asset_resource
    return BrandState(
        brand_key=manifest.brand_key,
        variant_key=variant.key,
        asset_resource=asset_resource,
        uses_default_asset=variant.asset_resource is None,
    )
