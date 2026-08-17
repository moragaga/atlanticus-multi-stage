from __future__ import annotations

from collections.abc import Mapping

from dash import html

from ada.contracts.tool_manifest import ToolManifest, ToolScope, ToolSectionKind
from ada.ui.components.component_container import build_component_container

from .errors import IntegratedOperationsLayoutError

_MINE_COMPONENT_KEYS = (
    'general_mina',
    'carguio',
    'transporte',
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
_SHARED_CARD_COMPONENT = 'carguio'
_SHARED_CARD_LINKED_COMPONENT = 'transporte'
_SHARED_CARD_SUBCOMPONENT = 'gestion_carguio_turno'


def build_integrated_operations_layout(
    manifest: ToolManifest,
    *,
    component_content: Mapping[str, object],
    shared_card_content: object,
    layout_id: str | None = None,
    class_name: str | None = None,
) -> html.Div:
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
    }
    if layout_id is not None:
        root_attributes['id'] = layout_id

    return html.Div(
        [
            _build_mine_scope(
                manifest,
                component_content=content,
                shared_card_content=shared_card_content,
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


def _build_mine_scope(
    manifest: ToolManifest,
    *,
    component_content: dict[str, object],
    shared_card_content: object,
) -> html.Section:
    scope_section = manifest.section(ToolScope.MINE.value)
    component_nodes = {
        component_key: _build_component(
            manifest,
            component_key=component_key,
            content=component_content[component_key],
        )
        for component_key in _MINE_COMPONENT_KEYS
    }
    shared = manifest.subcomponent(
        component=_SHARED_CARD_COMPONENT,
        subcomponent=_SHARED_CARD_SUBCOMPONENT,
    )
    return html.Section(
        [
            component_nodes['general_mina'],
            component_nodes['carguio'],
            component_nodes['transporte'],
            html.Div(
                shared_card_content,
                className=(
                    'ada-io-layout__shared-card ada-io-layout__shared-card--carguio-transporte'
                ),
                **{
                    'data-ada-io-shared-subcomponent-key': shared.key,
                },
            ),
            component_nodes['chancado_stmg'],
        ],
        className='ada-io-layout__scope ada-io-layout__scope--mine',
        **{
            'aria-label': scope_section.display_name,
            'data-ada-io-scope-key': ToolScope.MINE.value,
        },
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
    return build_component_container(
        manifest,
        component=component_key,
        content=content,
        class_name=f'ada-io-layout__component ada-io-layout__component--{component_key}',
    )


def _validate_layout_id(layout_id: str | None) -> None:
    if layout_id is not None and (not isinstance(layout_id, str) or not layout_id.strip()):
        raise IntegratedOperationsLayoutError(
            f'Invalid integrated operations layout id: {layout_id!r}'
        )


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

    shared = manifest.subcomponent(
        component=_SHARED_CARD_COMPONENT,
        subcomponent=_SHARED_CARD_SUBCOMPONENT,
    )
    linked_keys = {section.key for section in manifest.linked_components(shared.key)}
    if linked_keys != {_SHARED_CARD_COMPONENT, _SHARED_CARD_LINKED_COMPONENT}:
        raise IntegratedOperationsLayoutError(
            'Shared subcomponent "gestion_carguio_turno" must belong to "carguio" and "transporte"'
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
