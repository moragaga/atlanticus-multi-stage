# Espejo pedagógico de la implementación productiva.
# Conserva la misma estructura y comportamiento; los comentarios documentan su responsabilidad.
from dataclasses import dataclass

from ..errors import AlarmDefinitionError


@dataclass(frozen=True, slots=True)
class AlarmStatusState:
    active_count: int
    managed_count: int

    def __post_init__(self) -> None:
        if self.active_count < 0 or self.managed_count < 0:
            raise AlarmDefinitionError('Alarm status counts cannot be negative')
