# Espejo comentado: conserva exactamente la lógica productiva del módulo.
# Los comentarios describen la responsabilidad sin alterar el AST ejecutable.
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


class ProcessBodySection(StrEnum):
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'
    BOTTOM = 'bottom'
