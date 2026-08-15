# Los tres estados representan la presentación del mismo árbol DOM; el zoom no crea otra vista paralela.
from enum import StrEnum


class IntegratedOperationsView(StrEnum):
    OVERVIEW = 'overview'
    MINE = 'mine'
    PLANT = 'plant'
