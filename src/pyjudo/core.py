from abc import ABC, abstractmethod
from functools import partial
from typing import Any, Callable, Self

from pyjudo.service_entry import ServiceEntry
from pyjudo.service_life import ServiceLife


class IResolver(ABC):
    @abstractmethod
    def resolve[T](self, interface: type[T], overrides: dict[str, Any]) -> T: ...


class IServiceCache(ABC):
    @abstractmethod
    def get[T](self, interface: type[T]) -> T | None: ...

    @abstractmethod
    def add[T](self, interface: type[T], instance: T) -> None: ...

    @abstractmethod
    def __or__(self, other: Self | dict[type[Any], Any]) -> Self: ...

    @abstractmethod
    def __contains__(self, key: type) -> bool: ...


class IServiceRegistrar(ABC):
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
    def is_registered(self, interface: type) -> bool: ...

    @abstractmethod
    def add_transient[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> None: ...

    @abstractmethod
    def add_scoped[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> None: ...

    @abstractmethod
    def add_singleton[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> None: ...


class IServiceEntryCollection(ABC):
    @abstractmethod
    def get[T](self, interface: type[T]) -> ServiceEntry[T]: ...

    @abstractmethod
    def set[T](self, interface: type[T], entry: ServiceEntry[T]) -> None: ...

    @abstractmethod
    def remove[T](self, key: type[T]) -> None: ...

    @abstractmethod
    def __contains__(self, key: type) -> bool: ...


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


class IScopeStack(ABC):
    @abstractmethod
    def push(self, scope: IServiceScope) -> None: ...

    @abstractmethod
    def pop(self) -> None: ...

    @abstractmethod
    def get_current(self) -> IServiceScope | None: ...


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
    def is_registered(self, interface: type) -> bool: ...

    @abstractmethod
    def create_scope(self) -> IServiceScope: ...

    def __getitem__[T](self, key: type[T]) -> Callable[..., T]:
        return partial(self.get, key)