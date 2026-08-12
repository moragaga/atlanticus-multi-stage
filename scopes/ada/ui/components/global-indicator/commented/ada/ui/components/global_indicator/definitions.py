# Espejo comentado: conserva exactamente la lógica productiva del módulo.
# Los comentarios describen la responsabilidad sin alterar el AST ejecutable.
from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from .errors import GlobalIndicatorDefinitionError


def _remove_accent(*, text: str) -> str:
    return ''.join(
        letter
        for letter in unicodedata.normalize('NFD', text)
        if unicodedata.category(letter) != 'Mn'
    )


@dataclass(frozen=True, slots=True)
class IndicatorDefinition:
    temporality: str
    indicator_key: str
    only_last_measurement: bool = False

    def __post_init__(self) -> None:
        _require_text(self.temporality, field_name='temporality')
        _require_text(self.indicator_key, field_name='indicator_key')

    @property
    def temporality_key(self) -> str:
        return _remove_accent(text=self.temporality).casefold()

    @property
    def temporality_label(self) -> str:
        return self.temporality.capitalize()

    @property
    def real_kpi_key(self) -> str:
        return f'{self.indicator_key}_{self.temporality_key}_real_inst'

    @property
    def plan_kpi_key(self) -> str:
        return f'{self.indicator_key}_{self.temporality_key}_plan_inst'

    @property
    def color_kpi_key(self) -> str:
        return f'{self.indicator_key}_{self.temporality_key}_color_inst'


@dataclass(frozen=True, slots=True)
class IndicatorPropertiesDefinition:
    label: str
    temporality: str
    real_value: str
    plan_value: str
    last_measurement_label: str
    last_measurement_value: str

    def __post_init__(self) -> None:
        for field_name in (
            'label',
            'temporality',
            'real_value',
            'plan_value',
            'last_measurement_label',
            'last_measurement_value',
        ):
            _require_text(getattr(self, field_name), field_name=field_name)


@dataclass(frozen=True, slots=True)
class GlobalIndicatorDefinition:
    label: str
    unit: str
    properties: IndicatorPropertiesDefinition
    indicators: tuple[IndicatorDefinition, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'indicators', tuple(self.indicators))
        _require_text(self.label, field_name='label')
        _require_text(self.unit, field_name='unit')
        if not self.indicators:
            raise GlobalIndicatorDefinitionError(
                'Global indicator requires at least one measurement'
            )
        if sum(item.only_last_measurement for item in self.indicators) > 1:
            raise GlobalIndicatorDefinitionError(
                'Global indicator supports at most one last measurement'
            )
        keys = [(item.indicator_key, item.temporality_key) for item in self.indicators]
        if len(keys) != len(set(keys)):
            raise GlobalIndicatorDefinitionError('Global indicator contains duplicate measurements')


def _require_text(value: str, *, field_name: str) -> None:
    if not value.strip():
        raise GlobalIndicatorDefinitionError(f'{field_name} cannot be empty')
