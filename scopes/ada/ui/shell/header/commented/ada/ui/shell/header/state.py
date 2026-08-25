# Este espejo explica la validación de placements del Header contra el Tool Manifest.
# Un indicador compartido Mina/Planta debe colgar del destino global que expone ambos scopes.
from __future__ import annotations

from ada.contracts.tool_manifest import ToolManifest, ToolScope, ToolTarget
from ada.ui.components.branding import BrandState

from .errors import HeaderDefinitionError
from .models import HeaderBrandState, HeaderIndicatorPlacement, HeaderSectionStates, HeaderState


def create_header_state(
    *,
    manifest: ToolManifest,
    brand: BrandState,
    application_name: str,
    global_indicators: tuple[HeaderIndicatorPlacement, ...] = (),
    section_states: HeaderSectionStates | None = None,
    assistant_label: str = 'Asistente de decisiones ágiles',
) -> HeaderState:
    _require_header_structure(manifest)
    for placement in global_indicators:
        _validate_indicator_placement(manifest=manifest, placement=placement)

    return HeaderState(
        tool_key=manifest.tool_key,
        brand=HeaderBrandState(
            resolved_brand=brand,
            application_name=application_name,
            tool_name=manifest.display_name,
            assistant_label=assistant_label,
        ),
        global_indicators=global_indicators,
        section_states=section_states or HeaderSectionStates(),
    )


def _require_header_structure(manifest: ToolManifest) -> None:
    header = manifest.section('header')
    if header.scope is not ToolScope.GLOBAL:
        raise HeaderDefinitionError('Tool manifest header must use global scope')


def _validate_indicator_placement(
    *,
    manifest: ToolManifest,
    placement: HeaderIndicatorPlacement,
) -> None:
    if len(placement.scopes) == 1:
        _validate_scoped_section(
            manifest=manifest,
            section_key=placement.section_key,
            expected_scope=next(iter(placement.scopes)),
            required_ancestor='global_indicators',
            required_target=ToolTarget.KPI,
        )
        return
    _validate_shared_indicator_section(
        manifest=manifest,
        section_key=placement.section_key,
        scopes=placement.scopes,
    )


def _validate_shared_indicator_section(
    *,
    manifest: ToolManifest,
    section_key: str,
    scopes: frozenset[ToolScope],
) -> None:
    section = manifest.section(section_key)
    if section.scope is not ToolScope.GLOBAL:
        raise HeaderDefinitionError(
            f'Header section {section_key!r} must use global scope for shared indicators'
        )
    if not section.accepts(ToolTarget.KPI):
        raise HeaderDefinitionError(
            f'Header section {section_key!r} is not a valid kpi destination'
        )
    path_keys = tuple(item.key for item in manifest.path(section_key))
    if 'global_indicators' not in path_keys:
        raise HeaderDefinitionError(
            f"Header section {section_key!r} must belong to 'global_indicators'"
        )
    child_scopes = {
        child.scope for child in manifest.children(section_key) if child.accepts(ToolTarget.KPI)
    }
    if not scopes <= child_scopes:
        raise HeaderDefinitionError(
            f'Header section {section_key!r} does not expose all requested indicator scopes'
        )


def _validate_scoped_section(
    *,
    manifest: ToolManifest,
    section_key: str,
    expected_scope: ToolScope,
    required_ancestor: str,
    required_target: ToolTarget | None = None,
) -> None:
    section = manifest.section(section_key)
    if required_target is not None and not section.accepts(required_target):
        raise HeaderDefinitionError(
            f'Header section {section_key!r} is not a valid {required_target.value} destination'
        )
    if section.scope is not expected_scope:
        raise HeaderDefinitionError(
            f'Header section {section_key!r} scope does not match the indicator placement'
        )
    path_keys = tuple(item.key for item in manifest.path(section_key))
    if required_ancestor not in path_keys:
        raise HeaderDefinitionError(
            f'Header section {section_key!r} must belong to {required_ancestor!r}'
        )
