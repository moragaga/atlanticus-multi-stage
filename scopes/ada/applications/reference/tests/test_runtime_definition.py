from dataclasses import replace

from ada.applications.reference.runtime import (
    ADA_RUNTIME_SERVICE,
    build_reference_runtime_definition,
    create_reference_runtime_module,
)
from ada.contracts.tool_manifest import (
    INTEGRATED_OPERATIONS_MANIFEST,
    ToolSource,
    ToolSourceKey,
)
from ada.runtime.web import AdaRuntime, Freshness
from atlanticus.web.services import ServiceRegistry


def test_reference_runtime_definition_uses_manifest_source_policies() -> None:
    definition = build_reference_runtime_definition(INTEGRATED_OPERATIONS_MANIFEST)

    assert tuple(
        (source.key, source.stale_after_seconds) for source in definition.sources
    ) == (
        ('pi', 300),
        ('dispatch', 600),
    )


def test_reference_runtime_definition_does_not_invent_optional_sources() -> None:
    manifest = replace(
        INTEGRATED_OPERATIONS_MANIFEST,
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=420),),
    )

    definition = build_reference_runtime_definition(manifest)

    assert tuple(
        (source.key, source.stale_after_seconds) for source in definition.sources
    ) == (('pi', 420),)


def test_reference_runtime_only_publishes_sources_declared_by_manifest() -> None:
    manifest = replace(
        INTEGRATED_OPERATIONS_MANIFEST,
        sources=(ToolSource(ToolSourceKey.PI, stale_after_seconds=420),),
    )
    module = create_reference_runtime_module(manifest)
    services = ServiceRegistry()

    module.register_services(services)
    snapshot = services.require(ADA_RUNTIME_SERVICE, AdaRuntime).current().snapshot

    assert tuple(snapshot.sources) == ('pi',)
    assert snapshot.source('pi').freshness is Freshness.FRESH
