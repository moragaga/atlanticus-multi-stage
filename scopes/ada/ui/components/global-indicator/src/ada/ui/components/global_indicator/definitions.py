from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .errors import GlobalIndicatorDefinitionError
from .models import GlobalIndicatorMeasurementKind, GlobalIndicatorStyle

_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


def _remove_accent(*, text: str) -> str:
    return ''.join(
        letter
        for letter in unicodedata.normalize('NFD', text)
        if unicodedata.category(letter) != 'Mn'
    )


@dataclass(frozen=True, slots=True)
class GlobalIndicatorMeasurementDefinition:
    temporality: str
    source_key: str | None = None
    kind: GlobalIndicatorMeasurementKind = GlobalIndicatorMeasurementKind.TEMPORAL

    def __post_init__(self) -> None:
        _require_text(self.temporality, field_name='temporality')
        if self.source_key is not None:
            _require_key(self.source_key, field_name='source_key')

    @classmethod
    def temporal(
        cls,
        temporality: str,
        *,
        source_key: str | None = None,
    ) -> GlobalIndicatorMeasurementDefinition:
        return cls(temporality=temporality, source_key=source_key)

    @classmethod
    def last_measurement(
        cls,
        temporality: str = 'actual',
        *,
        source_key: str | None = None,
    ) -> GlobalIndicatorMeasurementDefinition:
        return cls(
            temporality=temporality,
            source_key=source_key,
            kind=GlobalIndicatorMeasurementKind.LAST_MEASUREMENT,
        )

    @property
    def temporality_key(self) -> str:
        return _remove_accent(text=self.temporality).casefold()

    @property
    def temporality_label(self) -> str:
        return self.temporality.capitalize()

    @property
    def is_last_measurement(self) -> bool:
        return self.kind is GlobalIndicatorMeasurementKind.LAST_MEASUREMENT

    def real_kpi_key(self, *, default_key: str) -> str:
        return f'{self._resolved_source_key(default_key)}_{self.temporality_key}_real_inst'

    def plan_kpi_key(self, *, default_key: str) -> str:
        return f'{self._resolved_source_key(default_key)}_{self.temporality_key}_plan_inst'

    def color_kpi_key(self, *, default_key: str) -> str:
        return f'{self._resolved_source_key(default_key)}_{self.temporality_key}_color_inst'

    def _resolved_source_key(self, default_key: str) -> str:
        return self.source_key or default_key


@dataclass(frozen=True, slots=True)
class GlobalIndicatorDefinition:
    key: str
    label: str
    unit: str
    measurements: tuple[GlobalIndicatorMeasurementDefinition, ...]
    definition_key: str | None = None
    style: GlobalIndicatorStyle = field(default_factory=GlobalIndicatorStyle)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'measurements', tuple(self.measurements))
        _require_key(self.key, field_name='key')
        _require_text(self.label, field_name='label')
        _require_text(self.unit, field_name='unit')
        if self.definition_key is not None:
            _require_key(self.definition_key, field_name='definition_key')
        if not self.measurements:
            raise GlobalIndicatorDefinitionError(
                'Global indicator requires at least one measurement'
            )
        if sum(item.is_last_measurement for item in self.measurements) > 1:
            raise GlobalIndicatorDefinitionError(
                'Global indicator supports at most one last measurement'
            )
        keys = [(item.source_key, item.temporality_key, item.kind) for item in self.measurements]
        if len(keys) != len(set(keys)):
            raise GlobalIndicatorDefinitionError(
                'Global indicator contains duplicate measurement definitions'
            )


def _require_text(value: str, *, field_name: str) -> None:
    if not value.strip():
        raise GlobalIndicatorDefinitionError(f'{field_name} cannot be empty')


def _require_key(value: str, *, field_name: str) -> None:
    if not _KEY_PATTERN.fullmatch(value):
        raise GlobalIndicatorDefinitionError(f'Invalid global indicator {field_name}: {value!r}')
