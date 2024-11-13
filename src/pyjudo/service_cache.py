import threading
from typing import override, Any


from pyjudo.core import IServiceCache


class ServiceCache(IServiceCache):
    def __init__(self, initial: dict[type[Any], Any] | None = None):
        self.__lock = threading.Lock()
        self._cache: dict[type[Any], Any] = initial or {}

    @override
    def get[T](self, interface: type[T]) -> T | None:
        with self.__lock:
            return self._cache.get(interface)

    @override
    def add[T](self, interface: type[T], instance: T) -> None:
        with self.__lock:
            self._cache[interface] = instance