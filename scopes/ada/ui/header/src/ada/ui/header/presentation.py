from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

from dash import html
from dash.development.base_component import Component

from ada.ui.branding import brand_asset_resource
from ada.ui.components.global_indicator import build_global_indicator

from .errors import HeaderPresentationError
from .models import (
    AlarmManagementSegmentState,
    AlarmManagementState,
    AlarmStatusState,
    HeaderGlobalIndicator,
    HeaderState,
)

_MIME_TYPES = {
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
}
_SCOPE_LABELS = {
    'mine': 'Mina',
    'plant': 'Planta',
}


def build_ada_header(
    state: HeaderState,
    *,
    desktop_navigation_trigger: Component | None = None,
    mobile_navigation_trigger: Component | None = None,
) -> html.Header:
    return html.Header(
        className='dashboard-header-shell ada-header-shell',
        **{
            'data-tool-key': state.tool_key,
            'data-application-name': state.brand.application_name,
            'data-brand-key': state.brand.brand.brand_key,
            'data-brand-variant': state.brand.brand.variant_key,
        },
        children=[
            html.Div(
                className='dashboard-header-inner ada-header',
                children=[
                    _build_brand(state),
                    html.Div(
                        className='ada-header__indicators',
                        children=[
                            _build_global_indicator_placement(placement)
                            for placement in state.global_indicators
                        ],
                    ),
                    build_alarm_management(state.alarm_management),
                    build_alarm_status(state.alarm_status),
                    html.Div(
                        mobile_navigation_trigger,
                        className='app-header-mobile-toggle ada-header__mobile-navigation',
                    )
                    if mobile_navigation_trigger is not None
                    else None,
                ],
            ),
            desktop_navigation_trigger,
        ],
    )


def build_alarm_management(state: AlarmManagementState | None) -> html.Div | None:
    if state is None:
        return None
    return html.Div(
        className='ada-header__management',
        children=[_build_management_segment(item) for item in state.segments],
    )


def build_alarm_status(state: AlarmStatusState | None) -> html.Div | None:
    if state is None:
        return None
    return html.Div(
        className='ada-header__alarm-status',
        **{'data-section-key': 'alarm_status', 'data-scope': 'global'},
        children=[
            html.Div('Alarmas', className='ada-header__alarm-status-label'),
            _build_alarm_status_chip(label='Activas', count=state.active_count),
            _build_alarm_status_chip(label='Gestionadas', count=state.managed_count),
        ],
    )


def _build_global_indicator_placement(placement: HeaderGlobalIndicator) -> html.Div:
    attributes = {
        'data-indicator-key': placement.key,
        'data-section-key': placement.section_key,
        'data-scope': placement.scope.value,
    }
    if placement.definition_key is not None:
        attributes['data-definition-key'] = placement.definition_key
    return html.Div(
        className='ada-header__global-indicator',
        **attributes,
        children=[build_global_indicator(model=placement.indicator)],
    )


def _build_brand(state: HeaderState) -> html.Div:
    brand = state.brand
    return html.Div(
        className='ada-header__brand',
        children=[
            html.Img(
                src=_brand_asset_data_uri(brand.brand.asset_resource),
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


def _build_management_segment(item: AlarmManagementSegmentState) -> html.Div:
    scope_label = _SCOPE_LABELS[item.scope.value]
    return html.Div(
        className='ada-header__management-segment',
        **{
            'data-section-key': item.section_key,
            'data-scope': item.scope.value,
            'data-tone': item.tone.value,
        },
        children=[
            html.Div(
                className='ada-header__management-group',
                children=[
                    html.Span(f'Grupo {scope_label}', className='ada-header__management-label'),
                    html.Strong(item.group_value, className='ada-header__management-value'),
                ],
            ),
            html.Div(
                className='ada-header__management-progress-block',
                children=[
                    html.Span(f'Gestión {scope_label}', className='ada-header__management-label'),
                    html.Strong(
                        f'{item.management_percentage:g}%',
                        className='ada-header__management-value',
                    ),
                    html.Progress(
                        value=item.management_percentage,
                        max=100,
                        className='ada-header__management-progress',
                        title=f'Gestión {scope_label}: {item.management_percentage:g}%',
                    ),
                ],
            ),
        ],
    )


def _build_alarm_status_chip(*, label: str, count: int) -> html.Div:
    return html.Div(
        className='ada-header__alarm-status-chip',
        children=[
            html.Span(str(count), className='ada-header__alarm-status-count'),
            html.Span(label, className='ada-header__alarm-status-text'),
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
