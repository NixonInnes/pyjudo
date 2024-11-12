from abc import ABC, abstractmethod
from typing import Any, Self


class IServiceCache(ABC):
    @abstractmethod
    def get[T](self, interface: type[T]) -> T | None: ...

    @abstractmethod
    def add[T](self, interface: type[T], instance: T) -> None: ...