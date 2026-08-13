# Construye el primer frame seguro; el ticker solo envejece la presentación en cliente.
from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from dash import html

from ada.runtime.web import Freshness, SourceHealth

from .models import TimeStatusSourceState, TimeStatusState

_SOURCE_ERROR_TEXT = {
    SourceHealth.UNAVAILABLE: 'Source unavailable',
    SourceHealth.INVALID: 'Invalid source data',
    SourceHealth.ERROR: 'Source error',
}
_SOURCE_ERROR_ICON = {
    SourceHealth.UNAVAILABLE: 'bi bi-cloud-slash',
    SourceHealth.INVALID: 'bi bi-exclamation-triangle',
    SourceHealth.ERROR: 'bi bi-cloud-slash',
}


def build_ada_time_status(
    state: TimeStatusState,
    *,
    now_utc: datetime | None = None,
) -> html.Section:
    now = _normalize_now(now_utc)
    return html.Section(
        className='ada-time-status',
        **{
            'aria-label': 'Estado temporal de fuentes',
            'data-ada-time-status': 'true',
            'data-tool-key': state.tool_key,
            'data-timezone': state.timezone,
        },
        children=[
            html.Div(
                className='ada-time-status__sources',
                children=[_build_source(source, now=now) for source in state.sources],
            ),
            _build_clock(state, now=now),
        ],
    )


def _build_source(source: TimeStatusSourceState, *, now: datetime) -> html.Div:
    freshness = _resolve_freshness(source, now=now)
    visual_state = _resolve_visual_state(source, freshness=freshness)
    updated_at = source.updated_at_utc
    attributes = {
        'data-time-status-source': 'true',
        'data-source-key': source.key.value,
        'data-source-health': source.runtime_state.health.value,
        'data-source-freshness': freshness.value,
        'data-stale-after-seconds': str(source.stale_after_seconds),
    }
    if updated_at is not None:
        attributes['data-updated-at-utc'] = (
            updated_at.isoformat().replace('+00:00', 'Z')
        )

    icon_class, value = _resolve_source_content(
        source, visual_state=visual_state, now=now
    )
    return html.Div(
        className=f'ada-time-status__source is-{visual_state}',
        **attributes,
        children=[
            html.Span(source.label, className='ada-time-status__source-label'),
            html.I(
                className=f'{icon_class} ada-time-status__source-icon',
                **{
                    'aria-hidden': 'true',
                    'data-time-status-icon': 'true',
                },
            ),
            html.Span(
                value,
                className='ada-time-status__source-value',
                **{'data-time-status-value': 'true'},
            ),
        ],
    )


def _build_clock(state: TimeStatusState, *, now: datetime) -> html.Div:
    value = now.astimezone(ZoneInfo(state.timezone)).strftime('%d-%m-%Y %H:%M:%S')
    return html.Div(
        className='ada-time-status__clock',
        children=[
            html.Span('Hora Actual', className='ada-time-status__clock-label'),
            html.I(
                className='bi bi-clock ada-time-status__clock-icon',
                **{'aria-hidden': 'true'},
            ),
            html.Span(
                value,
                className='ada-time-status__clock-value',
                **{'data-time-status-clock': 'true'},
            ),
        ],
    )


def _resolve_freshness(source: TimeStatusSourceState, *, now: datetime) -> Freshness:
    if source.runtime_state.health is not SourceHealth.HEALTHY:
        return Freshness.UNKNOWN
    if source.runtime_state.freshness is Freshness.STALE:
        return Freshness.STALE
    if source.updated_at_utc is None:
        return Freshness.UNKNOWN
    elapsed_seconds = max(0.0, (now - source.updated_at_utc).total_seconds())
    if elapsed_seconds >= source.stale_after_seconds:
        return Freshness.STALE
    return Freshness.FRESH


def _resolve_visual_state(
    source: TimeStatusSourceState,
    *,
    freshness: Freshness,
) -> str:
    if source.runtime_state.health is not SourceHealth.HEALTHY:
        return source.runtime_state.health.value
    return freshness.value


def _resolve_source_content(
    source: TimeStatusSourceState,
    *,
    visual_state: str,
    now: datetime,
) -> tuple[str, str]:
    health = source.runtime_state.health
    if health is not SourceHealth.HEALTHY:
        return _SOURCE_ERROR_ICON[health], _SOURCE_ERROR_TEXT[health]
    if source.updated_at_utc is None:
        return 'bi bi-exclamation-triangle', 'Invalid source data'
    elapsed_seconds = max(0, int((now - source.updated_at_utc).total_seconds()))
    icon = (
        'bi bi-cloud-slash'
        if visual_state == Freshness.STALE.value
        else 'bi bi-cloud-check'
    )
    return icon, format_elapsed_time(elapsed_seconds)


def format_elapsed_time(elapsed_seconds: int) -> str:
    if isinstance(elapsed_seconds, bool) or not isinstance(elapsed_seconds, int):
        raise ValueError('elapsed_seconds must be an integer')
    if elapsed_seconds < 0:
        raise ValueError('elapsed_seconds cannot be negative')
    if elapsed_seconds < 10:
        return 'hace menos de 10 segundos'
    if elapsed_seconds < 60:
        bucket = (elapsed_seconds // 10) * 10
        return f'hace más de {bucket} segundos'
    if elapsed_seconds < 3_600:
        minutes = elapsed_seconds // 60
        unit = 'minuto' if minutes == 1 else 'minutos'
        return f'hace más de {minutes} {unit}'
    if elapsed_seconds < 86_400:
        hours = elapsed_seconds // 3_600
        unit = 'hora' if hours == 1 else 'horas'
        return f'hace más de {hours} {unit}'
    days = elapsed_seconds // 86_400
    unit = 'día' if days == 1 else 'días'
    return f'hace más de {days} {unit}'


def _normalize_now(value: datetime | None) -> datetime:
    now = value or datetime.now(UTC)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError('now_utc must be timezone-aware')
    return now.astimezone(UTC)
