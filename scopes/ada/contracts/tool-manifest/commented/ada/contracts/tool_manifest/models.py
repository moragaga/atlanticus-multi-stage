# Espejo pedagógico: el manifest mantiene una jerarquía principal y permite vínculos adicionales solo para resolver casos compartidos sin duplicar entidades.
from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass

from .enums import (
    ProcessBodySection,
    ToolScope,
    ToolSectionKind,
    ToolSourceKey,
    ToolTarget,
)
from .errors import ToolManifestError, ToolManifestLookupError

_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


@dataclass(frozen=True, slots=True)
class ToolSource:
    key: ToolSourceKey
    stale_after_seconds: int

    def __post_init__(self) -> None:
        if not isinstance(self.key, ToolSourceKey):
            raise ToolManifestError(f'Invalid source key: {self.key!r}')
        if isinstance(self.stale_after_seconds, bool) or not isinstance(
            self.stale_after_seconds, int
        ):
            raise ToolManifestError('Source stale_after_seconds must be an integer')
        if self.stale_after_seconds <= 0:
            raise ToolManifestError('Source stale_after_seconds must be greater than zero')


@dataclass(frozen=True, slots=True, init=False)
class ToolSection:
    key: str
    display_name: str
    kind: ToolSectionKind
    scope: ToolScope
    parent_key: str | None
    targets: frozenset[ToolTarget]
    component: str | None
    subcomponent: str | None
    linked_component_keys: tuple[str, ...]
    layout_role: ProcessBodySection | None

    def __init__(
        self,
        *,
        display_name: str,
        kind: ToolSectionKind,
        scope: ToolScope,
        key: str | None = None,
        parent_key: str | None = None,
        targets: Iterable[ToolTarget] = (),
        component: str | None = None,
        subcomponent: str | None = None,
        linked_component_keys: Iterable[str] = (),
        layout_role: ProcessBodySection | None = None,
    ) -> None:
        if not isinstance(kind, ToolSectionKind):
            raise ToolManifestError(f'Invalid section kind: {kind!r}')
        if not isinstance(scope, ToolScope):
            raise ToolManifestError(f'Invalid section scope: {scope!r}')

        resolved_targets = frozenset(targets)
        if any(not isinstance(target, ToolTarget) for target in resolved_targets):
            raise ToolManifestError('Section targets must contain ToolTarget values')

        resolved_links = tuple(linked_component_keys)
        if len(resolved_links) != len(set(resolved_links)):
            raise ToolManifestError('Section linked_component_keys contains duplicates')

        _validate_display_name(display_name, field_name='section display_name')
        resolved_key, resolved_parent_key = _resolve_section_identity(
            kind=kind,
            key=key,
            parent_key=parent_key,
            component=component,
            subcomponent=subcomponent,
        )
        _validate_component_links_declaration(
            kind=kind,
            section_key=resolved_key,
            component=component,
            linked_component_keys=resolved_links,
        )
        _validate_layout_role_declaration(kind=kind, layout_role=layout_role)

        object.__setattr__(self, 'key', resolved_key)
        object.__setattr__(self, 'display_name', display_name)
        object.__setattr__(self, 'kind', kind)
        object.__setattr__(self, 'scope', scope)
        object.__setattr__(self, 'parent_key', resolved_parent_key)
        object.__setattr__(self, 'targets', resolved_targets)
        object.__setattr__(self, 'component', component)
        object.__setattr__(self, 'subcomponent', subcomponent)
        object.__setattr__(self, 'linked_component_keys', resolved_links)
        object.__setattr__(self, 'layout_role', layout_role)

    def accepts(self, target: ToolTarget) -> bool:
        return target in self.targets


@dataclass(frozen=True, slots=True)
class ToolManifest:
    tool_key: str
    display_name: str
    sources: tuple[ToolSource, ...]
    sections: tuple[ToolSection, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'sources', tuple(self.sources))
        object.__setattr__(self, 'sections', tuple(self.sections))
        _validate_key(self.tool_key, field_name='tool_key')
        _validate_display_name(self.display_name, field_name='display_name')
        _validate_sources(self.sources)
        if not self.sections:
            raise ToolManifestError('Tool manifest requires at least one section')
        _validate_sections(self.sections)

    def source(self, key: ToolSourceKey) -> ToolSource:
        for source in self.sources:
            if source.key is key:
                return source
        raise ToolManifestLookupError(f'Unknown source key: {key.value}')

    def has_source(self, key: ToolSourceKey) -> bool:
        return any(source.key is key for source in self.sources)

    def section(self, key: str) -> ToolSection:
        for section in self.sections:
            if section.key == key:
                return section
        raise ToolManifestLookupError(f'Unknown section key: {key}')

    def subcomponent(self, *, component: str, subcomponent: str) -> ToolSection:
        _validate_key(component, field_name='subcomponent component')
        _validate_key(subcomponent, field_name='subcomponent identity')
        direct_key = _build_subcomponent_key(component=component, subcomponent=subcomponent)
        for section in self.sections:
            if section.kind is not ToolSectionKind.SUBCOMPONENT:
                continue
            if section.key == direct_key:
                return section
            if (
                section.subcomponent == subcomponent
                and component in section.linked_component_keys
            ):
                return section
        raise ToolManifestLookupError(
            f'Unknown subcomponent for component {component!r}: {subcomponent!r}'
        )

    def roots(self) -> tuple[ToolSection, ...]:
        return tuple(section for section in self.sections if section.parent_key is None)

    def children(self, parent_key: str) -> tuple[ToolSection, ...]:
        self.section(parent_key)
        return tuple(section for section in self.sections if section.parent_key == parent_key)

    def path(self, section_key: str) -> tuple[ToolSection, ...]:
        current = self.section(section_key)
        resolved: list[ToolSection] = [current]
        while current.parent_key is not None:
            current = self.section(current.parent_key)
            resolved.append(current)
        resolved.reverse()
        return tuple(resolved)

    def sections_for_target(self, target: ToolTarget) -> tuple[ToolSection, ...]:
        return tuple(section for section in self.sections if section.accepts(target))

    def require_target(self, section_key: str, target: ToolTarget) -> ToolSection:
        section = self.section(section_key)
        if not section.accepts(target):
            raise ToolManifestLookupError(
                f'Section {section_key!r} does not accept target {target.value!r}'
            )
        return section

    def linked_components(self, section_key: str) -> tuple[ToolSection, ...]:
        section = self.section(section_key)
        if section.kind is ToolSectionKind.SUBCOMPONENT:
            component_keys = (section.component, *section.linked_component_keys)
            return tuple(
                self.section(component_key)
                for component_key in component_keys
                if component_key is not None
            )
        if section.kind is not ToolSectionKind.COMPONENT:
            raise ToolManifestLookupError(
                f'Section {section_key!r} cannot declare linked components'
            )
        return tuple(
            candidate
            for candidate in self.sections
            if candidate.kind is ToolSectionKind.COMPONENT
            and candidate.key != section.key
            and (
                candidate.key in section.linked_component_keys
                or section.key in candidate.linked_component_keys
            )
        )

    def component_for_layout_role(self, role: ProcessBodySection) -> ToolSection:
        if not isinstance(role, ProcessBodySection):
            raise ToolManifestLookupError(f'Invalid layout role: {role!r}')
        for section in self.sections:
            if section.layout_role is role:
                return section
        raise ToolManifestLookupError(f'Unknown layout role: {role.value}')


@dataclass(frozen=True, slots=True)
class ToolManifestRegistry:
    manifests: tuple[ToolManifest, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'manifests', tuple(self.manifests))
        keys = [manifest.tool_key for manifest in self.manifests]
        if len(keys) != len(set(keys)):
            raise ToolManifestError('Tool registry contains duplicate tool keys')

    def require(self, tool_key: str) -> ToolManifest:
        for manifest in self.manifests:
            if manifest.tool_key == tool_key:
                return manifest
        raise ToolManifestLookupError(f'Unknown tool key: {tool_key}')

    def sections_for_target(
        self,
        tool_key: str,
        target: ToolTarget,
    ) -> tuple[ToolSection, ...]:
        return self.require(tool_key).sections_for_target(target)


def _resolve_section_identity(
    *,
    kind: ToolSectionKind,
    key: str | None,
    parent_key: str | None,
    component: str | None,
    subcomponent: str | None,
) -> tuple[str, str | None]:
    if kind is ToolSectionKind.SUBCOMPONENT:
        if key is not None:
            raise ToolManifestError('Subcomponent key is generated internally')
        if parent_key is not None:
            raise ToolManifestError('Subcomponent parent_key is generated internally')
        if component is None or subcomponent is None:
            raise ToolManifestError('Subcomponent requires component and subcomponent identities')
        return (
            _build_subcomponent_key(component=component, subcomponent=subcomponent),
            component,
        )

    if key is None:
        raise ToolManifestError('Region and component sections require a key')
    if component is not None or subcomponent is not None:
        raise ToolManifestError(
            'Only subcomponents can declare component and subcomponent identities'
        )
    _validate_key(key, field_name='section key')
    if parent_key is not None:
        _validate_key(parent_key, field_name='section parent_key')
        if parent_key == key:
            raise ToolManifestError('Section cannot reference itself as parent')
    return key, parent_key


def _build_subcomponent_key(*, component: str, subcomponent: str) -> str:
    _validate_key(component, field_name='subcomponent component')
    _validate_key(subcomponent, field_name='subcomponent identity')
    return f'{component}_{subcomponent}'


def _validate_component_links_declaration(
    *,
    kind: ToolSectionKind,
    section_key: str,
    component: str | None,
    linked_component_keys: tuple[str, ...],
) -> None:
    if not linked_component_keys:
        return
    if kind not in {ToolSectionKind.COMPONENT, ToolSectionKind.SUBCOMPONENT}:
        raise ToolManifestError(
            'Only components and subcomponents can declare linked_component_keys'
        )
    for linked_key in linked_component_keys:
        _validate_key(linked_key, field_name='linked component key')
        if kind is ToolSectionKind.COMPONENT and linked_key == section_key:
            raise ToolManifestError('Component cannot link to itself')
        if kind is ToolSectionKind.SUBCOMPONENT and linked_key == component:
            raise ToolManifestError('Subcomponent cannot link to its parent component')


def _validate_layout_role_declaration(
    *,
    kind: ToolSectionKind,
    layout_role: ProcessBodySection | None,
) -> None:
    if layout_role is None:
        return
    if not isinstance(layout_role, ProcessBodySection):
        raise ToolManifestError(f'Invalid section layout role: {layout_role!r}')
    if kind is not ToolSectionKind.COMPONENT:
        raise ToolManifestError('Only components can declare a layout_role')


def _validate_sources(sources: tuple[ToolSource, ...]) -> None:
    if not sources:
        raise ToolManifestError('Tool manifest requires at least one source')
    keys = [source.key for source in sources]
    if len(keys) != len(set(keys)):
        raise ToolManifestError('Tool manifest contains duplicate source keys')
    if ToolSourceKey.PI not in keys:
        raise ToolManifestError('Tool manifest requires the pi source')


def _validate_sections(sections: tuple[ToolSection, ...]) -> None:
    by_key = {section.key: section for section in sections}
    if len(by_key) != len(sections):
        raise ToolManifestError('Tool manifest contains duplicate section keys')

    roles = [section.layout_role for section in sections if section.layout_role is not None]
    if len(roles) != len(set(roles)):
        raise ToolManifestError('Tool manifest contains duplicate layout roles')

    for section in sections:
        if section.parent_key is None:
            if section.kind is ToolSectionKind.SUBCOMPONENT:
                raise ToolManifestError('Subcomponent requires a parent component')
            continue

        parent = by_key.get(section.parent_key)
        if parent is None:
            raise ToolManifestError(
                f'Section {section.key!r} references unknown parent {section.parent_key!r}'
            )
        _validate_parent_kind(section=section, parent=parent)
        _validate_scope(section=section, parent=parent)

    _validate_component_links(sections=sections, by_key=by_key)
    _validate_subcomponent_aliases(sections=sections)

    for section in sections:
        _validate_no_cycle(section=section, by_key=by_key)


def _validate_component_links(
    *,
    sections: tuple[ToolSection, ...],
    by_key: dict[str, ToolSection],
) -> None:
    for section in sections:
        for linked_key in section.linked_component_keys:
            linked = by_key.get(linked_key)
            if linked is None:
                raise ToolManifestError(
                    f'Section {section.key!r} references unknown linked component {linked_key!r}'
                )
            if linked.kind is not ToolSectionKind.COMPONENT:
                raise ToolManifestError(
                    f'Section {section.key!r} can only link to a component'
                )
            if linked.scope is not section.scope:
                raise ToolManifestError(
                    f'Linked component {linked_key!r} scope must match section {section.key!r}'
                )


def _validate_subcomponent_aliases(*, sections: tuple[ToolSection, ...]) -> None:
    aliases: set[tuple[str, str]] = set()
    for section in sections:
        if section.kind is not ToolSectionKind.SUBCOMPONENT:
            continue
        if section.component is None or section.subcomponent is None:
            continue
        for component_key in (section.component, *section.linked_component_keys):
            alias = (component_key, section.subcomponent)
            if alias in aliases:
                raise ToolManifestError(
                    'Tool manifest contains duplicate subcomponent identity for component '
                    f'{component_key!r}: {section.subcomponent!r}'
                )
            aliases.add(alias)


def _validate_parent_kind(*, section: ToolSection, parent: ToolSection) -> None:
    if section.kind is ToolSectionKind.REGION and parent.kind is not ToolSectionKind.REGION:
        raise ToolManifestError('Region can only be nested under another region')
    if section.kind is ToolSectionKind.COMPONENT and parent.kind is not ToolSectionKind.REGION:
        raise ToolManifestError('Component can only be nested under a region')
    if (
        section.kind is ToolSectionKind.SUBCOMPONENT
        and parent.kind is not ToolSectionKind.COMPONENT
    ):
        raise ToolManifestError('Subcomponent can only be nested under a component')


def _validate_scope(*, section: ToolSection, parent: ToolSection) -> None:
    if parent.scope is ToolScope.GLOBAL:
        return
    if section.scope is not parent.scope:
        raise ToolManifestError(
            f'Section {section.key!r} scope must match non-global parent {parent.key!r}'
        )


def _validate_no_cycle(*, section: ToolSection, by_key: dict[str, ToolSection]) -> None:
    seen = {section.key}
    current = section
    while current.parent_key is not None:
        if current.parent_key in seen:
            raise ToolManifestError(f'Section hierarchy contains a cycle at {current.parent_key!r}')
        seen.add(current.parent_key)
        current = by_key[current.parent_key]


def _validate_key(value: str, *, field_name: str) -> None:
    if not _KEY_PATTERN.fullmatch(value):
        raise ToolManifestError(f'Invalid {field_name}: {value!r}')


def _validate_display_name(value: str, *, field_name: str) -> None:
    if not value.strip():
        raise ToolManifestError(f'{field_name} cannot be empty')
