from __future__ import annotations

from dash import html

from ada.ui.components.state_wrapper import ComponentCover, build_safe_state_wrapper

from .models import AlarmManagementSummarySegmentState, AlarmManagementSummaryState

_SCOPE_LABELS = {
    'mine': 'Mina',
    'plant': 'Planta',
}


def build_alarm_management_summary(
    state: AlarmManagementSummaryState | None,
    *,
    cover: ComponentCover | None = None,
) -> html.Div:
    return build_safe_state_wrapper(
        build_content=lambda: _build_content(state),
        cover=cover or ComponentCover.none(),
        ready_name='alarm-management',
    )


def _build_content(state: AlarmManagementSummaryState | None) -> html.Div | None:
    if state is None:
        return None
    return html.Div(
        className='ada-alarm-management-summary',
        children=[_build_segment(segment) for segment in state.segments],
    )


def _build_segment(segment: AlarmManagementSummarySegmentState) -> html.Div:
    scope_label = _SCOPE_LABELS[segment.scope.value]
    return html.Div(
        className='ada-alarm-management-summary__segment',
        **{
            'data-section-key': segment.section_key,
            'data-scope': segment.scope.value,
            'data-tone': segment.tone.value,
        },
        children=[
            html.Div(
                className='ada-alarm-management-summary__group',
                children=[
                    html.Span(
                        f'Grupo {scope_label}',
                        className='ada-alarm-management-summary__label',
                    ),
                    html.Strong(segment.group, className='ada-alarm-management-summary__value'),
                ],
            ),
            html.Div(
                className='ada-alarm-management-summary__progress-block',
                children=[
                    html.Span(
                        f'Gestión {scope_label}',
                        className='ada-alarm-management-summary__label',
                    ),
                    html.Strong(
                        f'{segment.management_percentage:g}%',
                        className='ada-alarm-management-summary__value',
                    ),
                    html.Progress(
                        value=segment.management_percentage,
                        max=100,
                        className='ada-alarm-management-summary__progress',
                        title=(f'Gestión {scope_label}: {segment.management_percentage:g}%'),
                    ),
                ],
            ),
        ],
    )
