from abc import ABC, abstractmethod
from typing import Any


class IResolver(ABC):
    @abstractmethod
    def resolve[T](self, interface: type[T], overrides: dict[str, Any]) -> T: ...