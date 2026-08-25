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
    wrapper_id: str | None = None,
) -> html.Section:
    section = manifest.section(component)
    if section.kind is not ToolSectionKind.COMPONENT:
        raise ComponentContainerDefinitionError(f'Section {component!r} is not a component')

    attributes: dict[str, Any] = {
        'aria-label': section.display_name,
        'data-ada-component-container': 'true',
        **component_identity_attributes(component),
    }
    resolved_wrapper_id = _resolve_wrapper_id(wrapper_id)
    if resolved_wrapper_id is not None:
        attributes['id'] = resolved_wrapper_id

    return html.Section(
        [
            html.Div(section.display_name, className='ada-component-container__title'),
            html.Div(content, className='ada-component-container__content'),
        ],
        className=_join_classes('ada-component-container', class_name),
        **attributes,
    )


def _resolve_wrapper_id(wrapper_id: str | None) -> str | None:
    if wrapper_id is None:
        return None
    if not isinstance(wrapper_id, str) or not wrapper_id.strip():
        raise ComponentContainerDefinitionError(
            f'Invalid component container wrapper id: {wrapper_id!r}'
        )
    return wrapper_id.strip()


def _join_classes(*values: str | None) -> str:
    return ' '.join(value.strip() for value in values if value and value.strip())
