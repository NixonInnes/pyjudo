from abc import ABC, abstractmethod
from typing import Any, Callable


class IResolver(ABC):
    @abstractmethod
    def resolve_anonymous[T](self, constructor: Callable[..., T], overrides: dict[str, Any], binding: Any | None = None) -> T: ...

    @abstractmethod
    def resolve[T](self, interface: type[T], overrides: dict[str, Any]) -> T: ...