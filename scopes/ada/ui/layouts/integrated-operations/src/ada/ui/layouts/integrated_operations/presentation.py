from __future__ import annotations

from collections.abc import Mapping

from dash import html

from ada.contracts.tool_manifest import ToolManifest, ToolScope, ToolSectionKind
from ada.ui.framework.core import component_identity_attributes

from .errors import IntegratedOperationsLayoutError
from .models import IntegratedOperationsView

_MINE_COMPONENT_KEYS = (
    'general_mina',
    'carguio',
    'transporte',
    'carguio_transporte',
    'chancado_stmg',
)
_PLANT_COMPONENT_KEYS = (
    'stockpile_chacay',
    'molienda',
    'flotacion',
    'transporte_fluidos',
    'puerto',
)
_REQUIRED_COMPONENT_KEYS = frozenset((*_MINE_COMPONENT_KEYS, *_PLANT_COMPONENT_KEYS))


def build_integrated_operations_layout(
    manifest: ToolManifest,
    *,
    component_content: Mapping[str, object],
    view: IntegratedOperationsView = IntegratedOperationsView.OVERVIEW,
    layout_id: str | None = None,
    class_name: str | None = None,
) -> html.Div:
    _validate_view(view)
    _validate_layout_id(layout_id)
    _validate_manifest(manifest)
    content = dict(component_content)
    _validate_content(content)

    classes = ' '.join(
        item
        for item in (
            'ada-io-layout',
            class_name,
        )
        if item
    )
    root_attributes = {
        'className': classes,
        'data-ada-io-layout': 'integrated-operations',
        'data-ada-io-view': view.value,
    }
    if layout_id is not None:
        root_attributes['id'] = layout_id

    return html.Div(
        [
            _build_scope(
                manifest,
                scope=ToolScope.MINE,
                component_keys=_MINE_COMPONENT_KEYS,
                component_content=content,
            ),
            _build_scope(
                manifest,
                scope=ToolScope.PLANT,
                component_keys=_PLANT_COMPONENT_KEYS,
                component_content=content,
            ),
        ],
        **root_attributes,
    )


def _build_scope(
    manifest: ToolManifest,
    *,
    scope: ToolScope,
    component_keys: tuple[str, ...],
    component_content: dict[str, object],
) -> html.Section:
    scope_section = manifest.section(scope.value)
    return html.Section(
        [
            _build_component(
                manifest,
                component_key=component_key,
                content=component_content[component_key],
            )
            for component_key in component_keys
        ],
        className=f'ada-io-layout__scope ada-io-layout__scope--{scope.value}',
        **{
            'aria-label': scope_section.display_name,
            'data-ada-io-scope-key': scope.value,
        },
    )


def _build_component(
    manifest: ToolManifest,
    *,
    component_key: str,
    content: object,
) -> html.Div:
    section = manifest.section(component_key)
    return html.Div(
        [
            html.Div(section.display_name, className='ada-io-layout__component-title'),
            html.Div(content, className='ada-io-layout__component-content'),
        ],
        className=f'ada-io-layout__component ada-io-layout__component--{component_key}',
        **{
            **component_identity_attributes(component_key),
            'aria-label': section.display_name,
        },
    )


def _validate_layout_id(layout_id: str | None) -> None:
    if layout_id is not None and (not isinstance(layout_id, str) or not layout_id.strip()):
        raise IntegratedOperationsLayoutError(
            f'Invalid integrated operations layout id: {layout_id!r}'
        )


def _validate_view(view: IntegratedOperationsView) -> None:
    if not isinstance(view, IntegratedOperationsView):
        raise IntegratedOperationsLayoutError(f'Invalid integrated operations view: {view!r}')


def _validate_manifest(manifest: ToolManifest) -> None:
    if not isinstance(manifest, ToolManifest):
        raise IntegratedOperationsLayoutError(f'Invalid tool manifest: {manifest!r}')
    if manifest.tool_key != 'integrated_operations':
        raise IntegratedOperationsLayoutError(
            'Integrated operations layout requires tool manifest '
            f'"integrated_operations", got {manifest.tool_key!r}'
        )

    _validate_scope(manifest, ToolScope.MINE, _MINE_COMPONENT_KEYS)
    _validate_scope(manifest, ToolScope.PLANT, _PLANT_COMPONENT_KEYS)

    linked_keys = {section.key for section in manifest.linked_components('carguio_transporte')}
    if linked_keys != {'carguio', 'transporte'}:
        raise IntegratedOperationsLayoutError(
            'Component "carguio_transporte" must be linked to "carguio" and "transporte"'
        )


def _validate_scope(
    manifest: ToolManifest,
    scope: ToolScope,
    component_keys: tuple[str, ...],
) -> None:
    scope_section = manifest.section(scope.value)
    if (
        scope_section.kind is not ToolSectionKind.REGION
        or scope_section.scope is not scope
        or scope_section.parent_key != 'body'
    ):
        raise IntegratedOperationsLayoutError(
            f'Section {scope.value!r} must be a {scope.value} region under body'
        )

    children = manifest.children(scope.value)
    child_keys = {section.key for section in children}
    expected_keys = set(component_keys)
    if child_keys != expected_keys:
        raise IntegratedOperationsLayoutError(
            f'Region {scope.value!r} does not match integrated operations geometry'
        )

    for component_key in component_keys:
        section = manifest.section(component_key)
        if section.kind is not ToolSectionKind.COMPONENT:
            raise IntegratedOperationsLayoutError(f'Section {component_key!r} must be a component')
        if section.scope is not scope or section.parent_key != scope.value:
            raise IntegratedOperationsLayoutError(
                f'Component {component_key!r} must belong to region {scope.value!r}'
            )


def _validate_content(component_content: dict[str, object]) -> None:
    keys = set(component_content)
    missing = sorted(_REQUIRED_COMPONENT_KEYS - keys)
    unexpected = sorted(keys - _REQUIRED_COMPONENT_KEYS)
    if missing:
        raise IntegratedOperationsLayoutError(
            f'Missing integrated operations component content: {", ".join(missing)}'
        )
    if unexpected:
        raise IntegratedOperationsLayoutError(
            f'Unexpected integrated operations component content: {", ".join(unexpected)}'
        )
