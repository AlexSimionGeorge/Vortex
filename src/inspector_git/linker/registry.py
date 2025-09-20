from __future__ import annotations
from typing import Optional
from uuid import UUID
from typing import TYPE_CHECKING

from src.common.registries import AbstractRegistry

if TYPE_CHECKING:
    from src.inspector_git.linker.models import Commit, File, Change
    from src.common.models import Account


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








