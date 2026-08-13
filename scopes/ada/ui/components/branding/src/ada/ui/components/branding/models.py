from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from .errors import BrandDefinitionError

_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
_RESOURCE_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]*$')


class BrandActivationRule(Protocol):
    def is_active(self, current_date: date) -> bool: ...


@dataclass(frozen=True, slots=True)
class MonthDayWindow:
    start_month: int
    start_day: int
    end_month: int
    end_day: int

    def __post_init__(self) -> None:
        _validate_month_day(self.start_month, self.start_day, field_name='start')
        _validate_month_day(self.end_month, self.end_day, field_name='end')

    def is_active(self, current_date: date) -> bool:
        current = (current_date.month, current_date.day)
        start = (self.start_month, self.start_day)
        end = (self.end_month, self.end_day)
        if start <= end:
            return start <= current <= end
        return current >= start or current <= end


@dataclass(frozen=True, slots=True)
class BrandVariant:
    key: str
    display_name: str
    activation_rule: BrandActivationRule
    asset_resource: str | None = None

    def __post_init__(self) -> None:
        _validate_key(self.key, field_name='variant key')
        _validate_display_name(self.display_name)
        if self.asset_resource is not None:
            _validate_resource_name(self.asset_resource)


@dataclass(frozen=True, slots=True)
class BrandManifest:
    brand_key: str
    default_asset_resource: str
    variants: tuple[BrandVariant, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'variants', tuple(self.variants))
        _validate_key(self.brand_key, field_name='brand key')
        _validate_resource_name(self.default_asset_resource)

        keys = [variant.key for variant in self.variants]
        if len(keys) != len(set(keys)):
            raise BrandDefinitionError('Brand manifest contains duplicate variant keys')
        if 'default' in keys or 'auto' in keys:
            raise BrandDefinitionError('Brand variant key is reserved')

    def variant(self, key: str) -> BrandVariant:
        for variant in self.variants:
            if variant.key == key:
                return variant
        raise BrandDefinitionError(f'Unknown brand variant: {key!r}')


@dataclass(frozen=True, slots=True)
class BrandContext:
    current_date: date
    requested_variant: str = 'auto'

    def __post_init__(self) -> None:
        if self.requested_variant not in {'auto', 'default'}:
            _validate_key(self.requested_variant, field_name='requested variant')


@dataclass(frozen=True, slots=True)
class BrandState:
    brand_key: str
    variant_key: str
    asset_resource: str
    uses_default_asset: bool


def _validate_key(value: str, *, field_name: str) -> None:
    if not _KEY_PATTERN.fullmatch(value):
        raise BrandDefinitionError(f'Invalid {field_name}: {value!r}')


def _validate_display_name(value: str) -> None:
    if not value.strip():
        raise BrandDefinitionError('Brand variant display_name cannot be empty')


def _validate_resource_name(value: str) -> None:
    if not _RESOURCE_PATTERN.fullmatch(value):
        raise BrandDefinitionError(f'Invalid brand asset resource: {value!r}')


def _validate_month_day(month: int, day: int, *, field_name: str) -> None:
    try:
        date(2000, month, day)
    except ValueError as exc:
        raise BrandDefinitionError(f'Invalid {field_name} month/day') from exc
