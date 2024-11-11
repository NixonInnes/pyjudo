from typing import override, Any, Self

from pyjudo.core import IServiceCache


class ServiceCache(IServiceCache):
    def __init__(self, initial: dict[type[Any], Any] | None = None):
        self._cache: dict[type[Any], Any] = initial or {}

    @override
    def get[T](self, interface: type[T]) -> T | None:
        return self._cache.get(interface)

    @override
    def add[T](self, interface: type[T], instance: T) -> None:
        self._cache[interface] = instance

    @override
    def __or__(self, other: Self | dict[type[Any], Any]) -> Self:
        if isinstance(other, ServiceCache):
            return self.__class__(self._cache | other._cache)
        return self.__class__(self._cache | other)

    @override
    def __contains__(self, key: type) -> bool:
        return key in self._cache