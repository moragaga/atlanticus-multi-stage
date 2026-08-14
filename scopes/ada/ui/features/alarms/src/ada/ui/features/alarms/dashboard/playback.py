from __future__ import annotations

from enum import StrEnum

from ..errors import AlarmDefinitionError


class AlarmPresentationInteraction(StrEnum):
    INTERACTIVE = 'interactive'
    VIEW_ONLY = 'view-only'


def alarm_presentation_scope_attributes(
    *,
    trace_dwell_ms: int,
    interaction: AlarmPresentationInteraction,
) -> dict[str, str]:
    if not isinstance(trace_dwell_ms, int) or isinstance(trace_dwell_ms, bool):
        raise AlarmDefinitionError(f'Invalid alarm trace dwell: {trace_dwell_ms!r}')
    if trace_dwell_ms <= 0:
        raise AlarmDefinitionError(f'Invalid alarm trace dwell: {trace_dwell_ms!r}')
    if not isinstance(interaction, AlarmPresentationInteraction):
        raise AlarmDefinitionError(f'Invalid alarm presentation interaction: {interaction!r}')
    return {
        'data-ada-alarm-presentation-scope': 'true',
        'data-ada-alarm-trace-dwell-ms': str(trace_dwell_ms),
        'data-ada-alarm-interaction': interaction.value,
    }
