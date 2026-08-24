# El adapter separa la base ADA del comportamiento concreto de cada tipo de superficie.
from __future__ import annotations

from typing import Protocol

from ada.contracts.tool_manifest import ToolManifest

from .models import AdaSurfaceComposition


class AdaSurfaceAdapter(Protocol):
    @property
    def key(self) -> str: ...

    def supports(self, manifest: ToolManifest) -> bool: ...

    def compose(self, manifest: ToolManifest) -> AdaSurfaceComposition: ...
