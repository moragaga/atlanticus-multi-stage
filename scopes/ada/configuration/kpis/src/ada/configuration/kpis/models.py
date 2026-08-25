from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ada.configuration.kpis.errors import KpiConfigurationValidationError
from ada.configuration.kpis.identity import require_identity_key


@dataclass(frozen=True, slots=True)
class KpiBinding:
    key: str
    destination_keys: tuple[str, ...]
    latest_enabled: bool = True
    series_enabled: bool = False
    series_hours: int | None = None

    def __post_init__(self) -> None:
        key = require_identity_key(self.key, label='KPI key')
        destinations = tuple(
            require_identity_key(value, label='KPI destination key')
            for value in self.destination_keys
        )
        if not destinations:
            raise KpiConfigurationValidationError(
                'KPI binding must define at least one destination'
            )
        if len(destinations) != len(set(destinations)):
            raise KpiConfigurationValidationError('KPI destination keys must be unique')
        if not isinstance(self.latest_enabled, bool):
            raise KpiConfigurationValidationError('KPI latest flag must be boolean')
        if not isinstance(self.series_enabled, bool):
            raise KpiConfigurationValidationError('KPI series flag must be boolean')
        if self.series_enabled:
            if (
                isinstance(self.series_hours, bool)
                or not isinstance(self.series_hours, int)
                or self.series_hours <= 0
            ):
                raise KpiConfigurationValidationError(
                    'KPI series hours must be a positive integer when series is enabled'
                )
        elif self.series_hours is not None:
            raise KpiConfigurationValidationError(
                'KPI series hours must be empty when series is disabled'
            )
        object.__setattr__(self, 'key', key)
        object.__setattr__(self, 'destination_keys', destinations)

    @property
    def enabled(self) -> bool:
        return self.latest_enabled or self.series_enabled

    def to_document(self) -> dict[str, object]:
        return {
            'key': self.key,
            'destination_keys': list(self.destination_keys),
            'latest_enabled': self.latest_enabled,
            'series_enabled': self.series_enabled,
            'series_hours': self.series_hours,
        }

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> KpiBinding:
        try:
            destinations = document['destination_keys']
            latest_enabled = document.get('latest_enabled', True)
            series_enabled = document.get('series_enabled', False)
            series_hours = document.get('series_hours')
            if not isinstance(destinations, list):
                raise TypeError
            if not isinstance(latest_enabled, bool) or not isinstance(series_enabled, bool):
                raise TypeError
            if series_hours is not None and (
                isinstance(series_hours, bool) or not isinstance(series_hours, int)
            ):
                raise TypeError
            return cls(
                key=str(document['key']),
                destination_keys=tuple(str(value) for value in destinations),
                latest_enabled=latest_enabled,
                series_enabled=series_enabled,
                series_hours=series_hours,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise KpiConfigurationValidationError('KPI binding contract is invalid') from error


@dataclass(frozen=True, slots=True)
class KpiConfiguration:
    bindings: tuple[KpiBinding, ...] = ()

    def __post_init__(self) -> None:
        bindings = tuple(self.bindings)
        keys = tuple(binding.key for binding in bindings)
        if len(keys) != len(set(keys)):
            raise KpiConfigurationValidationError('KPI keys must be unique')
        object.__setattr__(self, 'bindings', bindings)

    def binding(self, key: str) -> KpiBinding | None:
        normalized = require_identity_key(key, label='KPI key')
        return next((binding for binding in self.bindings if binding.key == normalized), None)

    def add_binding(self, binding: KpiBinding) -> KpiConfiguration:
        if self.binding(binding.key) is not None:
            raise KpiConfigurationValidationError('KPI key already exists')
        return KpiConfiguration(self.bindings + (binding,))

    def replace_binding(self, binding: KpiBinding) -> KpiConfiguration:
        if self.binding(binding.key) is None:
            raise KpiConfigurationValidationError('KPI key does not exist')
        return KpiConfiguration(
            tuple(binding if item.key == binding.key else item for item in self.bindings)
        )

    def remove_binding(self, key: str) -> KpiConfiguration:
        normalized = require_identity_key(key, label='KPI key')
        if self.binding(normalized) is None:
            raise KpiConfigurationValidationError('KPI key does not exist')
        return KpiConfiguration(
            tuple(binding for binding in self.bindings if binding.key != normalized)
        )

    def to_document(self) -> dict[str, object]:
        return {'bindings': [binding.to_document() for binding in self.bindings]}

    @classmethod
    def from_document(cls, document: dict[str, Any]) -> KpiConfiguration:
        try:
            bindings = document.get('bindings', [])
            if not isinstance(bindings, list) or not all(
                isinstance(item, dict) for item in bindings
            ):
                raise TypeError
            return cls(bindings=tuple(KpiBinding.from_document(dict(item)) for item in bindings))
        except (TypeError, ValueError) as error:
            raise KpiConfigurationValidationError(
                'KPI configuration contract is invalid'
            ) from error
