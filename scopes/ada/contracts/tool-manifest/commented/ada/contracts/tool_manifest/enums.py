from enum import StrEnum


# Clasifica el rol estructural de cada nodo sin describir su CSS o layout físico.
class ToolSectionKind(StrEnum):
    REGION = 'region'
    COMPONENT = 'component'
    SUBCOMPONENT = 'subcomponent'


# Normaliza los ámbitos transversales que hoy necesita ADA.
class ToolScope(StrEnum):
    GLOBAL = 'global'
    MINE = 'mine'
    PLANT = 'plant'
    PROCESS = 'process'


# Define qué configuradores pueden seleccionar una sección como destino válido.
class ToolTarget(StrEnum):
    KPI = 'kpi'
    ALARM = 'alarm'


# Normaliza las regiones visuales disponibles para herramientas ADA Process.
class ProcessBodySection(StrEnum):
    LEFT = 'left'
    CENTER = 'center'
    RIGHT = 'right'
    BOTTOM = 'bottom'
