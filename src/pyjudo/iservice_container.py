from abc import ABC, abstractmethod
from functools import partial
from typing import Any, Callable, Self

from pyjudo.service_life import ServiceLife


class IServiceContainer(ABC):
    @abstractmethod
    def register[T](
        self,
        abstract_class: type[T],
        service_class: type[T],
        service_life: ServiceLife = ServiceLife.TRANSIENT,
    ) -> Self: ...

    @abstractmethod
    def add_transient[T](self, abstract_class: type[T], service_class: type[T]) -> Self: ...

    @abstractmethod
    def add_scoped[T](self, abstract_class: type[T], service_class: type[T]) -> Self: ...

    @abstractmethod
    def add_singleton[T](self, abstract_class: type[T], service_class: type[T]) -> Self: ...

    @abstractmethod
    def get[T](self, abstract_class: type[T], **overrides: Any) -> T: ... # pyright: ignore[reportAny]

    def __getitem__[T](self, key: type[T]) -> Callable[..., T]:
        return partial(self.get, key)