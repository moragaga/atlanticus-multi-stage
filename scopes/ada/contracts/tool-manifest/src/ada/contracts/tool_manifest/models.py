from __future__ import annotations

import re
from dataclasses import dataclass, field

from .enums import ToolScope, ToolSectionKind, ToolTarget
from .errors import ToolManifestError, ToolManifestLookupError

_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')


@dataclass(frozen=True, slots=True)
class ToolSection:
    key: str
    display_name: str
    kind: ToolSectionKind
    scope: ToolScope
    parent_key: str | None = None
    targets: frozenset[ToolTarget] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        object.__setattr__(self, 'targets', frozenset(self.targets))
        _validate_key(self.key, field_name='section key')
        _validate_display_name(self.display_name, field_name='section display_name')
        if self.parent_key is not None:
            _validate_key(self.parent_key, field_name='section parent_key')
            if self.parent_key == self.key:
                raise ToolManifestError('Section cannot reference itself as parent')

    def accepts(self, target: ToolTarget) -> bool:
        return target in self.targets


@dataclass(frozen=True, slots=True)
class ToolManifest:
    tool_key: str
    display_name: str
    sections: tuple[ToolSection, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, 'sections', tuple(self.sections))
        _validate_key(self.tool_key, field_name='tool_key')
        _validate_display_name(self.display_name, field_name='display_name')
        if not self.sections:
            raise ToolManifestError('Tool manifest requires at least one section')
        _validate_sections(self.sections)

    def section(self, key: str) -> ToolSection:
        for section in self.sections:
            if section.key == key:
                return section
        raise ToolManifestLookupError(f'Unknown section key: {key}')

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


def _validate_sections(sections: tuple[ToolSection, ...]) -> None:
    by_key = {section.key: section for section in sections}
    if len(by_key) != len(sections):
        raise ToolManifestError('Tool manifest contains duplicate section keys')

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

    for section in sections:
        _validate_no_cycle(section=section, by_key=by_key)


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
