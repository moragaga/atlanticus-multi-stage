class RuntimeDefinitionError(ValueError):
    """Raised when an ADA runtime contract is structurally invalid."""


class SharedSnapshotConsistencyError(RuntimeError):
    """Raised when a shared snapshot does not match its advertised revision."""
