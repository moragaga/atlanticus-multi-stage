from __future__ import annotations

from collections.abc import Mapping

from dash import html

from ada.contracts.tool_manifest import (
    ProcessBodySection,
    ToolManifest,
    ToolManifestLookupError,
    ToolSection,
    ToolSectionKind,
)
from ada.ui.components.component_container import build_component_container
from ada.ui.framework.core import slot_identity_attributes

from .errors import ProcessLayoutError


def build_process_layout(
    manifest: ToolManifest,
    *,
    component_content: Mapping[str, object],
    component_wrapper_ids: Mapping[str, str] | None = None,
    layout_id: str | None = None,
    class_name: str | None = None,
) -> html.Div:
    _validate_layout_id(layout_id)
    components = _resolve_components(manifest)
    content = dict(component_content)
    _validate_content(components, content)
    wrapper_ids = {} if component_wrapper_ids is None else dict(component_wrapper_ids)

    root_attributes = {
        'className': _join_classes('ada-process-layout', class_name),
        'data-ada-process-layout': 'process',
    }
    if layout_id is not None:
        root_attributes['id'] = layout_id

    main_components = tuple(
        component
        for role in (
            ProcessBodySection.LEFT,
            ProcessBodySection.CENTER,
            ProcessBodySection.RIGHT,
        )
        if (component := components.get(role)) is not None
    )
    children = [
        html.Div(
            [
                _build_slot(
                    manifest,
                    component=component,
                    content=content[component.key],
                    wrapper_id=wrapper_ids.get(component.key),
                    width=_main_width(role=component.layout_role, components=components),
                )
                for component in main_components
            ],
            className='row g-1 mx-0 ada-process-layout__main',
        )
    ]
    bottom = components.get(ProcessBodySection.BOTTOM)
    if bottom is not None:
        children.append(
            html.Div(
                [
                    _build_slot(
                        manifest,
                        component=bottom,
                        content=content[bottom.key],
                        wrapper_id=wrapper_ids.get(bottom.key),
                        width=12,
                    )
                ],
                className='row g-1 mx-0 ada-process-layout__bottom',
            )
        )

    return html.Div(children, **root_attributes)


def _build_slot(
    manifest: ToolManifest,
    *,
    component: ToolSection,
    content: object,
    wrapper_id: str | None,
    width: int,
) -> html.Section:
    role = component.layout_role
    if role is None:
        raise ProcessLayoutError(f'Process component {component.key!r} requires a layout role')
    return html.Section(
        build_component_container(
            manifest,
            component=component.key,
            content=content,
            class_name='ada-process-layout__component',
            wrapper_id=wrapper_id,
        ),
        className=f'col-{width} ada-process-layout__slot ada-process-layout__slot--{role.value}',
        **{
            'aria-label': component.display_name,
            'data-ada-process-layout-role': role.value,
            'data-ada-process-component-key': component.key,
            **slot_identity_attributes(role.value),
        },
    )


def _resolve_components(manifest: ToolManifest) -> dict[ProcessBodySection, ToolSection]:
    if not isinstance(manifest, ToolManifest):
        raise ProcessLayoutError(f'Invalid tool manifest: {manifest!r}')
    try:
        body = manifest.section('body')
    except ToolManifestLookupError as exc:
        raise ProcessLayoutError('Process layout requires a body region') from exc
    if body.kind is not ToolSectionKind.REGION:
        raise ProcessLayoutError('Process layout body must be a region')

    components: dict[ProcessBodySection, ToolSection] = {}
    for section in manifest.children('body'):
        if section.kind is not ToolSectionKind.COMPONENT or section.layout_role is None:
            raise ProcessLayoutError('Process body direct children must be layout components')
        components[section.layout_role] = section
    if ProcessBodySection.CENTER not in components:
        raise ProcessLayoutError('Process layout requires the center layout role')
    return components


def _main_width(
    *,
    role: ProcessBodySection | None,
    components: dict[ProcessBodySection, ToolSection],
) -> int:
    if role is None or role is ProcessBodySection.BOTTOM:
        raise ProcessLayoutError(f'Invalid main process layout role: {role!r}')
    has_left = ProcessBodySection.LEFT in components
    has_right = ProcessBodySection.RIGHT in components
    if role is ProcessBodySection.LEFT:
        return 2
    if role is ProcessBodySection.RIGHT:
        return 2
    if has_left and has_right:
        return 8
    if has_left or has_right:
        return 10
    return 12


def _validate_content(
    components: dict[ProcessBodySection, ToolSection],
    content: dict[str, object],
) -> None:
    expected = {section.key for section in components.values()}
    keys = set(content)
    missing = sorted(expected - keys)
    unexpected = sorted(keys - expected)
    if missing:
        raise ProcessLayoutError(f'Missing process component content: {", ".join(missing)}')
    if unexpected:
        raise ProcessLayoutError(f'Unexpected process component content: {", ".join(unexpected)}')


def _validate_layout_id(layout_id: str | None) -> None:
    if layout_id is not None and (not isinstance(layout_id, str) or not layout_id.strip()):
        raise ProcessLayoutError(f'Invalid process layout id: {layout_id!r}')


def _join_classes(*values: str | None) -> str:
    return ' '.join(value for value in values if value)
