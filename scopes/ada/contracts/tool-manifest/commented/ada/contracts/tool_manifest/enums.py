from enum import StrEnum


class ToolSectionKind(StrEnum):
    REGION = 'region'
    COMPONENT = 'component'
    SUBCOMPONENT = 'subcomponent'


class ToolScope(StrEnum):
    GLOBAL = 'global'
    MINE = 'mine'
    PLANT = 'plant'


class ToolTarget(StrEnum):
    KPI = 'kpi'
    ALARM = 'alarm'


# Catálogo explícito de fuentes que hoy forman parte del contrato ADA.
class ToolSourceKey(StrEnum):
    PI = 'pi'
    DISPATCH = 'dispatch'


# Estado de la resolución externa del manifest; no degrada la validez del contrato.
class ToolManifestResolutionStatus(StrEnum):
    READY = 'ready'
    NOT_PROJECTED = 'not_projected'
    INVALID = 'invalid'
    SOURCE_ERROR = 'source_error'


class ProcessBodySection(StrEnum):
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'
    BOTTOM = 'bottom'
