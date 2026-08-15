from __future__ import annotations

from typing import Any

from dash import html

from ada.contracts.tool_manifest import ToolManifest, ToolSectionKind
from ada.ui.framework.core import component_identity_attributes

from .errors import ComponentContainerDefinitionError


def build_component_container(
    manifest: ToolManifest,
    *,
    component: str,
    content: Any = None,
    class_name: str | None = None,
) -> html.Section:
    section = manifest.section(component)
    if section.kind is not ToolSectionKind.COMPONENT:
        raise ComponentContainerDefinitionError(f'Section {component!r} is not a component')

    return html.Section(
        [
            html.Div(section.display_name, className='ada-component-container__title'),
            html.Div(content, className='ada-component-container__content'),
        ],
        className=_join_classes('ada-component-container', class_name),
        **{
            'aria-label': section.display_name,
            'data-ada-component-container': 'true',
            **component_identity_attributes(component),
        },
    )


def _join_classes(*values: str | None) -> str:
    return ' '.join(value.strip() for value in values if value and value.strip())
