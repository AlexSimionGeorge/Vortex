from enum import Enum, auto

class ChangeType(Enum):
    """Enum representing the type of change that occurred to a file."""
    Add = auto()
    Delete = auto()
    Rename = auto()
    Modify = auto()

class HunkType(Enum):
    """Enum representing the type of change that occurred in a hunk."""
    Add = auto()
    Delete = auto()
    Modify = auto()

class LineOperation(Enum):
    """Enum representing whether a line was added or deleted."""
    Add = auto()
    Delete = auto()