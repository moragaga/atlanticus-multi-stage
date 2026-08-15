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

from .errors import ProcessLayoutError


def build_process_layout(
    manifest: ToolManifest,
    *,
    region_content: Mapping[str, object],
    layout_id: str | None = None,
    class_name: str | None = None,
) -> html.Div:
    _validate_layout_id(layout_id)
    regions = _resolve_regions(manifest)
    content = dict(region_content)
    _validate_content(regions, content)

    root_attributes = {
        'className': _join_classes('ada-process-layout', class_name),
        'data-ada-process-layout': 'process',
    }
    if layout_id is not None:
        root_attributes['id'] = layout_id

    main_regions = tuple(
        region
        for role in (
            ProcessBodySection.LEFT,
            ProcessBodySection.CENTER,
            ProcessBodySection.RIGHT,
        )
        if (region := regions.get(role)) is not None
    )
    children = [
        html.Div(
            [
                _build_region(
                    region,
                    content=content[region.key],
                    width=_main_width(role=region.layout_role, regions=regions),
                )
                for region in main_regions
            ],
            className='row g-1 mx-0 ada-process-layout__main',
        )
    ]
    bottom = regions.get(ProcessBodySection.BOTTOM)
    if bottom is not None:
        children.append(
            html.Div(
                [_build_region(bottom, content=content[bottom.key], width=12)],
                className='row g-1 mx-0 ada-process-layout__bottom',
            )
        )

    return html.Div(children, **root_attributes)


def _build_region(section: ToolSection, *, content: object, width: int) -> html.Section:
    role = section.layout_role
    if role is None:
        raise ProcessLayoutError(f'Process region {section.key!r} requires a layout role')
    return html.Section(
        [
            html.Div(section.display_name, className='ada-process-layout__region-title'),
            html.Div(content, className='ada-process-layout__region-content'),
        ],
        className=(
            f'col-{width} ada-process-layout__region ada-process-layout__region--{role.value}'
        ),
        **{
            'aria-label': section.display_name,
            'data-ada-process-region-key': section.key,
            'data-ada-process-layout-role': role.value,
        },
    )


def _resolve_regions(manifest: ToolManifest) -> dict[ProcessBodySection, ToolSection]:
    if not isinstance(manifest, ToolManifest):
        raise ProcessLayoutError(f'Invalid tool manifest: {manifest!r}')
    try:
        body = manifest.section('body')
    except ToolManifestLookupError as exc:
        raise ProcessLayoutError('Process layout requires a body region') from exc
    if body.kind is not ToolSectionKind.REGION:
        raise ProcessLayoutError('Process layout body must be a region')

    regions: dict[ProcessBodySection, ToolSection] = {}
    for section in manifest.children('body'):
        if section.kind is not ToolSectionKind.REGION or section.layout_role is None:
            raise ProcessLayoutError('Process body direct children must be layout regions')
        regions[section.layout_role] = section
    if ProcessBodySection.CENTER not in regions:
        raise ProcessLayoutError('Process layout requires the center layout role')
    return regions


def _main_width(
    *,
    role: ProcessBodySection | None,
    regions: dict[ProcessBodySection, ToolSection],
) -> int:
    if role is None or role is ProcessBodySection.BOTTOM:
        raise ProcessLayoutError(f'Invalid main process layout role: {role!r}')
    has_left = ProcessBodySection.LEFT in regions
    has_right = ProcessBodySection.RIGHT in regions
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
    regions: dict[ProcessBodySection, ToolSection],
    content: dict[str, object],
) -> None:
    expected = {section.key for section in regions.values()}
    keys = set(content)
    missing = sorted(expected - keys)
    unexpected = sorted(keys - expected)
    if missing:
        raise ProcessLayoutError(f'Missing process region content: {", ".join(missing)}')
    if unexpected:
        raise ProcessLayoutError(f'Unexpected process region content: {", ".join(unexpected)}')


def _validate_layout_id(layout_id: str | None) -> None:
    if layout_id is not None and (not isinstance(layout_id, str) or not layout_id.strip()):
        raise ProcessLayoutError(f'Invalid process layout id: {layout_id!r}')


def _join_classes(*values: str | None) -> str:
    return ' '.join(value for value in values if value)
