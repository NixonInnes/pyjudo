import threading
from typing import Any, override

from pyjudo.core import IServiceEntryCollection, ServiceEntry
from pyjudo.exceptions import ServiceRegistrationError, ServiceResolutionError


class ServiceEntryCollection(IServiceEntryCollection):
    def __init__(self):
        self.__lock = threading.Lock()
        self._entries: dict[type[Any], ServiceEntry[Any]] = {}

    @override
    def get[T](self, interface: type[T]) -> ServiceEntry[T]:
        with self.__lock:
            entry = self._entries.get(interface)
        if entry is None:
            raise ServiceResolutionError(
                f"No service registered for: {interface.__name__}"
            )
        return entry

    @override
    def set[T](self, interface: type[T], entry: ServiceEntry[T]) -> None:
        with self.__lock:
            if interface in self._entries:
                raise ServiceRegistrationError(
                    f"Service '{interface.__name__}' is already registered."
                )
            self._entries[interface] = entry

    @override
    def remove[T](self, key: type[T]) -> None:
        _ = self._entries.pop(key, None)

    @override
    def __contains__(self, key: type) -> bool:
        return key in self._entries