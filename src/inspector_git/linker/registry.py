from __future__ import annotations
from typing import Generic, TypeVar, Dict, Collection, Set
from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.inspector_git.linker.models import Account, Commit, File, Change

TYPE = TypeVar("TYPE")
ID = TypeVar("ID")


class AbstractRegistry(Generic[TYPE, ID], ABC):
    def __init__(self) -> None:
        self._map: Dict[ID, TYPE] = {}

    @property
    def all(self) -> Collection[TYPE]:
        return self._map.values()

    @property
    def all_ids(self) -> Set[ID]:
        return set(self._map.keys())

    def get_by_id(self, id: ID) -> Optional[TYPE]:
        return self._map.get(id)

    def contains(self, id: ID) -> bool:
        return id in self._map

    def add(self, entity: TYPE, id: Optional[ID] = None) -> Optional[TYPE]:
        if id is None:
            id = self.get_id(entity)
        return self._map.setdefault(id, entity)

    def add_all(self, entities: Collection[TYPE]) -> None:
        for entity in entities:
            self._map[self.get_id(entity)] = entity

    def remove(self, id: ID) -> Optional[TYPE]:
        return self._map.pop(id, None)

    def delete(self, entity: TYPE) -> Optional[TYPE]:
        return self._map.pop(self.get_id(entity), None)

    def is_empty(self) -> bool:
        return len(self._map) == 0

    @abstractmethod
    def get_id(self, entity: TYPE) -> ID:
        ...

class AccountRegistry(AbstractRegistry["Account", str]):
    def get_id(self, entity: "Account") -> str:
        return entity.id

class CommitRegistry(AbstractRegistry["Commit", str]):
    def get_by_id(self, id: str) -> Optional["Commit"]:
        if id.startswith("^"):
            return self._find_by_prefix(id.removeprefix("^"))
        return super().get_by_id(id)

    def contains(self, id: str) -> bool:
        if id.startswith("^"):
            return self._find_by_prefix(id.removeprefix("^")) is not None
        return super().contains(id)

    def _find_by_prefix(self, prefix: str) -> Optional["Commit"]:
        return next((commit for commit in self.all if commit.id.startswith(prefix)), None)

    def get_id(self, entity: "Commit") -> str:
        return entity.id

class FileRegistry(AbstractRegistry["File", UUID]):
    def get_id(self, entity: "File") -> UUID:
        return entity.id

class ChangeRegistry(AbstractRegistry["Change", str]):
    def get_id(self, entity: "Change") -> str:
        return entity.id








