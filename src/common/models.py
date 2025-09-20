from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar
from pydantic import BaseModel, Field


class Project(BaseModel, ABC):
    linked_projects: set[Project] = Field(default_factory=set)

    class Config:
        arbitrary_types_allowed = True

    def link(self, other: Project) -> None:
        self.linked_projects.add(other)

    def is_linked(self, other: Project) -> bool:
        return other in self.linked_projects


class Account(BaseModel, ABC):
    name: str
    project: Optional[Project] = None
    developer: Optional[Developer] = None

    class Config:
        arbitrary_types_allowed = True

    @property
    @abstractmethod
    def id(self) -> str:
        ...

    def __eq__(self, other: object) -> bool:
        if self is other:
            return True
        if not isinstance(other, Account):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)


AccountType = TypeVar("AccountType", bound=Account)
class Developer(BaseModel):
    name: str
    accounts: list[Account] = Field(default_factory=list)

    def get_accounts_of_type(self, account_type: Type[AccountType]) -> list[AccountType]:
        return [account for account in self.accounts if isinstance(account, account_type)]

    class Config:
        arbitrary_types_allowed = True


Account.model_rebuild()

__all__ = ["Account", "Developer", "Project"]