from dataclasses import dataclass

import pytest
from dash import html

from ada.compositions.surface import (
    AdaSurfaceAdapterError,
    AdaSurfaceComposition,
    AdaSurfaceLookupError,
    AdaSurfaceRegistry,
)
from ada.contracts.tool_manifest import (
    ToolManifest,
    ToolScope,
    ToolSection,
    ToolSectionKind,
    ToolSource,
    ToolSourceKey,
)
from atlanticus.web.modules import WebModule
from atlanticus.web.services import ServiceRegistry


@dataclass(frozen=True, slots=True)
class FakeAdapter:
    key: str
    supported_tool_key: str

    def supports(self, manifest: ToolManifest) -> bool:
        return manifest.tool_key == self.supported_tool_key

    def compose(self, manifest: ToolManifest) -> AdaSurfaceComposition:
        return AdaSurfaceComposition(
            adapter_key=self.key,
            manifest=manifest,
            modules=(WebModule(name=f'{self.key}-module'),),
            builder=lambda _services: html.Div(
                manifest.display_name,
                **{'data-test-surface': self.key},
            ),
        )


def test_registry_resolves_different_surface_adapters_without_runtime_conditionals() -> None:
    registry = AdaSurfaceRegistry(
        (
            FakeAdapter('integrated_operations', 'integrated_operations'),
            FakeAdapter('process', 'flotation_process'),
        )
    )

    integrated = registry.compose(_manifest('integrated_operations'))
    process = registry.compose(_manifest('flotation_process'))

    assert integrated.adapter_key == 'integrated_operations'
    assert process.adapter_key == 'process'
    assert integrated.modules[0].name == 'integrated_operations-module'
    assert process.modules[0].name == 'process-module'
    assert integrated.build(ServiceRegistry()).to_plotly_json()['props']['data-test-surface'] == (
        'integrated_operations'
    )
    assert (
        process.build(ServiceRegistry()).to_plotly_json()['props']['data-test-surface'] == 'process'
    )


def test_registry_rejects_duplicate_adapter_keys() -> None:
    with pytest.raises(AdaSurfaceAdapterError, match='duplicate adapter keys'):
        AdaSurfaceRegistry(
            (
                FakeAdapter('surface', 'one'),
                FakeAdapter('surface', 'two'),
            )
        )


def test_registry_rejects_unsupported_manifest() -> None:
    registry = AdaSurfaceRegistry((FakeAdapter('integrated_operations', 'integrated_operations'),))

    with pytest.raises(AdaSurfaceLookupError, match='No surface adapter supports'):
        registry.compose(_manifest('unknown_tool'))


def test_registry_rejects_ambiguous_manifest_support() -> None:
    manifest = _manifest('integrated_operations')
    registry = AdaSurfaceRegistry(
        (
            FakeAdapter('one', manifest.tool_key),
            FakeAdapter('two', manifest.tool_key),
        )
    )

    with pytest.raises(AdaSurfaceLookupError, match='Multiple surface adapters support'):
        registry.compose(manifest)


def _manifest(tool_key: str) -> ToolManifest:
    return ToolManifest(
        tool_key=tool_key,
        display_name=tool_key.replace('_', ' ').title(),
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=300),),
        sections=(
            ToolSection(
                key='body',
                display_name='Body',
                kind=ToolSectionKind.REGION,
                scope=ToolScope.GLOBAL,
            ),
        ),
    )


def test_adapters_can_keep_distinct_internal_alarm_baselines() -> None:
    @dataclass(frozen=True, slots=True)
    class AlarmBehaviorAdapter:
        key: str
        supported_tool_key: str
        alarm_baseline: str

        def supports(self, manifest: ToolManifest) -> bool:
            return manifest.tool_key == self.supported_tool_key

        def compose(self, manifest: ToolManifest) -> AdaSurfaceComposition:
            return AdaSurfaceComposition(
                adapter_key=self.key,
                manifest=manifest,
                modules=(),
                builder=lambda _services: html.Div(
                    **{'data-test-alarm-baseline': self.alarm_baseline}
                ),
            )

    registry = AdaSurfaceRegistry(
        (
            AlarmBehaviorAdapter(
                'integrated_operations',
                'integrated_operations',
                'integrated-operations-baseline',
            ),
            AlarmBehaviorAdapter('process', 'flotation_process', 'process-baseline'),
        )
    )

    integrated = registry.compose(_manifest('integrated_operations')).build(ServiceRegistry())
    process = registry.compose(_manifest('flotation_process')).build(ServiceRegistry())

    assert integrated.to_plotly_json()['props']['data-test-alarm-baseline'] == (
        'integrated-operations-baseline'
    )
    assert process.to_plotly_json()['props']['data-test-alarm-baseline'] == 'process-baseline'
