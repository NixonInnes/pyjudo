from abc import ABC, abstractmethod

from .iservice_scope import IServiceScope


class IScopeStack(ABC):
    @abstractmethod
    def push(self, scope: IServiceScope) -> None: ...

    @abstractmethod
    def pop(self) -> None: ...

    @abstractmethod
    def get_current(self) -> IServiceScope | None: ...