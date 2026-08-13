# Espejo pedagógico de la implementación productiva.
# Conserva la misma estructura y comportamiento; los comentarios documentan su responsabilidad.
from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

from dash import html
from dash.development.base_component import Component

from ada.ui.components.branding import brand_asset_resource
from ada.ui.components.global_indicator import build_global_indicator
from ada.ui.components.state_wrapper import build_safe_state_wrapper

from .errors import HeaderPresentationError
from .models import HeaderIndicatorPlacement, HeaderState

_MIME_TYPES = {
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
}


# Header define la geometría de sus slots, pero no conoce modelos ni renderers de Alarmas.
def build_ada_header(
    state: HeaderState,
    *,
    alarm_management_slot: Component | None = None,
    alarm_status_slot: Component | None = None,
    desktop_navigation_trigger: Component | None = None,
    mobile_navigation_trigger: Component | None = None,
) -> html.Header:
    inner_children: list[Component] = [
        _build_brand(state),
        _build_indicators_slot(state),
        _build_management_slot(alarm_management_slot),
        _build_alarm_status_slot(alarm_status_slot),
    ]
    if mobile_navigation_trigger is not None:
        inner_children.append(
            html.Div(
                mobile_navigation_trigger,
                className='app-header-mobile-toggle ada-header__mobile-navigation',
            )
        )

    children: list[Component] = [
        html.Div(
            className='dashboard-header-inner ada-header',
            children=inner_children,
        )
    ]
    if desktop_navigation_trigger is not None:
        children.append(desktop_navigation_trigger)

    return html.Header(
        className='dashboard-header-shell ada-header-shell',
        **{
            'data-tool-key': state.tool_key,
            'data-application-name': state.brand.application_name,
            'data-brand-key': state.brand.resolved_brand.brand_key,
            'data-brand-variant': state.brand.resolved_brand.variant_key,
        },
        children=children,
    )


def _build_indicators_slot(state: HeaderState) -> html.Div:
    content = html.Div(
        className='ada-header__indicators',
        children=[
            _build_global_indicator_placement(placement) for placement in state.global_indicators
        ],
    )
    return html.Div(
        className='ada-header__indicators-slot',
        **{'data-section-key': 'global_indicators'},
        children=[
            build_safe_state_wrapper(
                build_content=lambda: content,
                cover=state.section_states.global_indicators,
                ready_name='global-indicators',
            )
        ],
    )


def _build_management_slot(content: Component | None) -> html.Div:
    return html.Div(
        className='ada-header__management-slot',
        **{'data-section-key': 'alarm_management'},
        children=[] if content is None else [content],
    )


def _build_alarm_status_slot(content: Component | None) -> html.Div:
    return html.Div(
        className='ada-header__alarm-status-slot',
        **{'data-section-key': 'alarm_status'},
        children=[] if content is None else [content],
    )


def _build_global_indicator_placement(placement: HeaderIndicatorPlacement) -> html.Div:
    attributes = {
        'data-indicator-key': placement.indicator.key,
        'data-section-key': placement.section_key,
        'data-scope': placement.scope.value,
    }
    if placement.indicator.definition_key is not None:
        attributes['data-definition-key'] = placement.indicator.definition_key
    return html.Div(
        className='ada-header__global-indicator',
        **attributes,
        children=[
            build_safe_state_wrapper(
                build_content=lambda: build_global_indicator(state=placement.indicator),
            )
        ],
    )


def _build_brand(state: HeaderState) -> html.Div:
    brand = state.brand
    return html.Div(
        className='ada-header__brand',
        children=[
            html.Img(
                src=_brand_asset_data_uri(brand.resolved_brand.asset_resource),
                alt=brand.application_name,
                title=brand.application_name,
                className='ada-header__brand-logo',
            ),
            html.Div(
                className='ada-header__brand-lockup',
                children=[
                    html.Div(brand.assistant_label, className='ada-header__brand-assistant'),
                    html.Div(
                        className='ada-header__brand-tool',
                        children=[
                            html.Span(className='ada-header__brand-rule'),
                            html.Span(brand.tool_name),
                            html.Span(className='ada-header__brand-rule'),
                        ],
                    ),
                ],
            ),
        ],
    )


@lru_cache(maxsize=16)
def _brand_asset_data_uri(resource_name: str) -> str:
    suffix = Path(resource_name).suffix.lower()
    mime_type = _MIME_TYPES.get(suffix)
    if mime_type is None:
        raise HeaderPresentationError(f'Unsupported brand asset type: {suffix!r}')
    resource = brand_asset_resource(resource_name)
    try:
        payload = resource.read_bytes()
    except (FileNotFoundError, OSError) as exc:
        raise HeaderPresentationError('Brand asset is not available') from exc
    encoded = base64.b64encode(payload).decode('ascii')
    return f'data:{mime_type};base64,{encoded}'
