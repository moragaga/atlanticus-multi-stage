from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from datetime import UTC, datetime

from ada.runtime.component_stores import RuntimeComponentStoreRegistry
from ada.runtime.delivery_cache import DeliveryChannel, DeliverySnapshot

from .errors import RuntimeDeliveryCollectorError


@dataclass(frozen=True, slots=True)
class RuntimeChannelUpdatePlan:
    control: dict[str, object] | None
    component_payloads: tuple[dict[str, object] | None, ...]

    @classmethod
    def unchanged(cls, component_count: int) -> RuntimeChannelUpdatePlan:
        return cls(control=None, component_payloads=(None,) * component_count)


def plan_channel_updates(
    *,
    channel: DeliveryChannel,
    snapshot: DeliverySnapshot | None,
    registry: RuntimeComponentStoreRegistry,
    current_control: Mapping[str, object] | None,
    current_payloads: Sequence[object],
) -> RuntimeChannelUpdatePlan:
    component_count = len(registry.components)
    if len(current_payloads) != component_count:
        raise RuntimeDeliveryCollectorError(
            'Runtime collector current payload count does not match the component registry'
        )
    if snapshot is None:
        return RuntimeChannelUpdatePlan.unchanged(component_count)
    if not _should_accept_snapshot(snapshot=snapshot, current_control=current_control):
        return RuntimeChannelUpdatePlan.unchanged(component_count)
    if channel is DeliveryChannel.LATEST:
        candidate_payloads = _latest_payloads(snapshot=snapshot, registry=registry)
    elif channel is DeliveryChannel.TIMESERIES:
        candidate_payloads = _timeseries_payloads(snapshot=snapshot, registry=registry)
    else:
        raise RuntimeDeliveryCollectorError(f'Unsupported delivery channel: {channel!r}')
    updates = tuple(
        candidate if candidate != current else None
        for candidate, current in zip(candidate_payloads, current_payloads, strict=True)
    )
    return RuntimeChannelUpdatePlan(
        control=_build_control(snapshot),
        component_payloads=updates,
    )


def _latest_payloads(
    *,
    snapshot: DeliverySnapshot,
    registry: RuntimeComponentStoreRegistry,
) -> tuple[dict[str, object], ...]:
    destinations = _require_mapping(snapshot.payload.get('destinations'), 'Latest destinations')
    payloads: list[dict[str, object]] = []
    for component in registry.components:
        if component.component_key not in destinations:
            payloads.append({'state': 'unmapped', 'items': {}})
            continue
        items = _require_mapping(
            destinations[component.component_key],
            f'Latest destination {component.component_key!r}',
        )
        payloads.append({'state': 'mapped', 'items': deepcopy(dict(items))})
    return tuple(payloads)


def _timeseries_payloads(
    *,
    snapshot: DeliverySnapshot,
    registry: RuntimeComponentStoreRegistry,
) -> tuple[dict[str, object], ...]:
    destinations = _require_mapping(
        snapshot.payload.get('destinations'),
        'Timeseries destinations',
    )
    windows = _require_sequence(snapshot.payload.get('windows'), 'Timeseries windows')
    normalized_windows: tuple[Mapping[str, object], ...] = tuple(
        _require_mapping(window, 'Timeseries window') for window in windows
    )
    payloads: list[dict[str, object]] = []
    for component in registry.components:
        if component.component_key not in destinations:
            payloads.append({'state': 'unmapped', 'windows': []})
            continue
        keys = _require_string_sequence(
            destinations[component.component_key],
            f'Timeseries destination {component.component_key!r}',
        )
        component_windows: list[dict[str, object]] = []
        for window in normalized_windows:
            destination = window.get('destination')
            if not isinstance(destination, str) or not destination.strip():
                raise RuntimeDeliveryCollectorError(
                    'Timeseries window destination must be a non-empty string'
                )
            if destination.strip() == component.component_key:
                component_windows.append(deepcopy(dict(window)))
        payloads.append(
            {
                'state': 'mapped',
                'keys': list(keys),
                'windows': component_windows,
            }
        )
    return tuple(payloads)


def _should_accept_snapshot(
    *,
    snapshot: DeliverySnapshot,
    current_control: Mapping[str, object] | None,
) -> bool:
    if not current_control:
        return True
    revision = current_control.get('revision')
    if revision is None:
        return True
    if not isinstance(revision, str) or not revision.strip():
        raise RuntimeDeliveryCollectorError('Runtime delivery control revision is invalid')
    if revision.strip() == snapshot.revision:
        return False
    published = _parse_control_timestamp(current_control.get('published_at_utc'))
    if snapshot.published_at_utc <= published:
        return False
    return True


def _build_control(snapshot: DeliverySnapshot) -> dict[str, object]:
    return {
        'revision': snapshot.revision,
        'published_at_utc': snapshot.published_at_utc.astimezone(UTC)
        .isoformat()
        .replace('+00:00', 'Z'),
    }


def _parse_control_timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value:
        raise RuntimeDeliveryCollectorError('Runtime delivery control publication time is invalid')
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError as error:
        raise RuntimeDeliveryCollectorError(
            'Runtime delivery control publication time is invalid'
        ) from error
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise RuntimeDeliveryCollectorError('Runtime delivery control publication time is invalid')
    return parsed.astimezone(UTC)


def _require_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RuntimeDeliveryCollectorError(f'{label} must be a mapping')
    for key in value:
        if not isinstance(key, str) or not key:
            raise RuntimeDeliveryCollectorError(f'{label} keys must be non-empty strings')
    return value


def _require_sequence(value: object, label: str) -> Sequence[object]:
    if not isinstance(value, Sequence) or isinstance(value, str | bytes | bytearray):
        raise RuntimeDeliveryCollectorError(f'{label} must be a sequence')
    return value


def _require_string_sequence(value: object, label: str) -> tuple[str, ...]:
    sequence = _require_sequence(value, label)
    normalized: list[str] = []
    for item in sequence:
        if not isinstance(item, str) or not item.strip():
            raise RuntimeDeliveryCollectorError(f'{label} must contain non-empty strings')
        normalized.append(item.strip())
    return tuple(normalized)
