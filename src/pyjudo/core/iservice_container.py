from abc import ABC, abstractmethod
from functools import partial
from typing import Any, Callable, Self

from .service_life import ServiceLife
from .iservice_scope import IServiceScope


class IServiceContainer(ABC):
    @abstractmethod
    def register[T](
        self,
        interface: type[T],
        constructor: type[T] | Callable[..., T],
        lifetime: ServiceLife = ServiceLife.TRANSIENT,
    ) -> None: ...

    @abstractmethod
    def unregister(self, interface: type) -> None: ...

    @abstractmethod
    def add_transient[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> Self: ...

    @abstractmethod
    def add_scoped[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> Self: ...

    @abstractmethod
    def add_singleton[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> Self: ...

    @abstractmethod
    def get[T](self, interface: type[T], **overrides: Any) -> T: ...

    @abstractmethod
    def get_factory[T](self, interface: type[T]) -> Callable[..., T]: ...

    @abstractmethod
    def is_registered(self, interface: type) -> bool: ...

    @abstractmethod
    def create_scope(self) -> IServiceScope: ...

    def __getitem__[T](self, key: type[T]) -> Callable[..., T]:
        return partial(self.get, key)