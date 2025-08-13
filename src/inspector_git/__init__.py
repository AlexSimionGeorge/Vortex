"""Inspector Git - .iglog parser (Python)

Exposes:
- IGLogReader: Reader for .iglog files
- Pydantic models: GitLogDTO, CommitDTO, ChangeDTO, HunkDTO, LineChangeDTO
- Enums: ChangeType, HunkType, LineOperation
- Constants: IGLogConstants
- Helper: to_pretty_json
"""

from src.inspector_git.data_structures.constants import IGLogConstants
from .reader import IGLogReader
from src.inspector_git.data_structures.models import (
    GitLogDTO,
    CommitDTO,
    ChangeDTO,
    HunkDTO,
    LineChangeDTO,
    ChangeType,
    HunkType,
    LineOperation,
    to_pretty_json,
)

__all__ = [
    "IGLogConstants",
    "IGLogReader",
    "GitLogDTO",
    "CommitDTO",
    "ChangeDTO",
    "HunkDTO",
    "LineChangeDTO",
    "ChangeType",
    "HunkType",
    "LineOperation",
    "to_pretty_json",
]