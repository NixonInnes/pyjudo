from abc import ABC, abstractmethod
from typing import Any, Callable, Self


class IServiceScope(ABC):
    @abstractmethod
    def get[T](self, interface: type[T], **overrides: Any) -> T: ...

    @abstractmethod
    def get_instance[T](self, interface: type[T]) -> T | None: ...

    @abstractmethod
    def add_instance[T](self, interface: type[T], instance: T) -> None: ...

    @abstractmethod
    def __getitem__[T](self, key: type[T]) -> Callable[..., T]: ...

    @abstractmethod
    def __enter__(self) -> Self: ...

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback) -> None: ...