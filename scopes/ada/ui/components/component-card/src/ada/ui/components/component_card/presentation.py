from __future__ import annotations

import logging
from typing import Any

from dash import html

from ada.contracts.tool_manifest import ToolManifest, ToolSectionKind
from ada.ui.framework.core import subcomponent_identity_attributes

from .errors import ComponentCardDefinitionError

_LOGGER = logging.getLogger(__name__)
_MISSING = object()


def build_component_card(
    manifest: ToolManifest,
    *,
    component: str,
    subcomponent: str,
    content: Any = None,
    label: str | None = None,
    corner: bool = False,
    corner_value: Any = _MISSING,
    overlay: Any = None,
    class_name: str | None = None,
    wrapper_id: str | None = None,
) -> html.Div:
    component_section = manifest.section(component)
    if component_section.kind is not ToolSectionKind.COMPONENT:
        raise ComponentCardDefinitionError(f'Section {component!r} is not a component')

    section = manifest.subcomponent(component=component, subcomponent=subcomponent)
    if section.kind is not ToolSectionKind.SUBCOMPONENT:
        raise ComponentCardDefinitionError(f'Section {section.key!r} is not a subcomponent')

    resolved_corner_value = _resolve_corner_value(
        component=component,
        subcomponent=subcomponent,
        corner=corner,
        corner_value=corner_value,
    )
    footer = _build_footer(
        label=label,
        corner=corner,
        corner_value=resolved_corner_value,
    )
    children: list[Any] = [
        html.Div(
            content,
            className='ada-component-card__content',
        )
    ]
    if footer is not None:
        children.append(footer)
    if overlay is not None:
        children.append(overlay)

    attributes: dict[str, Any] = {
        'aria-label': section.display_name,
        'data-ada-component-card': 'true',
        'data-ada-component-card-component-key': component,
        **subcomponent_identity_attributes(section.key),
    }
    resolved_wrapper_id = _resolve_wrapper_id(wrapper_id)
    if resolved_wrapper_id is not None:
        attributes['id'] = resolved_wrapper_id

    return html.Div(
        children,
        className=_join_classes('ada-component-card', class_name),
        **attributes,
    )


def _resolve_wrapper_id(wrapper_id: str | None) -> str | None:
    if wrapper_id is None:
        return None
    if not isinstance(wrapper_id, str) or not wrapper_id.strip():
        raise ComponentCardDefinitionError(f'Invalid component card wrapper id: {wrapper_id!r}')
    return wrapper_id.strip()


def _resolve_corner_value(
    *,
    component: str,
    subcomponent: str,
    corner: bool,
    corner_value: Any,
) -> Any:
    if not corner:
        return _MISSING
    if corner_value is not _MISSING:
        return corner_value
    _LOGGER.warning(
        'ComponentCard corner value was not provided; rendering an empty value. '
        'component=%s subcomponent=%s',
        component,
        subcomponent,
    )
    return ''


def _build_footer(
    *,
    label: str | None,
    corner: bool,
    corner_value: Any,
) -> html.Div | None:
    if label is None and not corner:
        return None

    children: list[Any] = []
    if label is not None:
        children.append(
            html.Span(
                label,
                className='ada-component-card__footer-label',
            )
        )
    if corner:
        children.append(
            html.Span(
                corner_value,
                className='ada-component-card__footer-corner',
                **{'data-ada-component-card-corner': 'true'},
            )
        )
    return html.Div(
        children,
        className='ada-component-card__footer',
    )


def _join_classes(*values: str | None) -> str:
    return ' '.join(value.strip() for value in values if value and value.strip())
