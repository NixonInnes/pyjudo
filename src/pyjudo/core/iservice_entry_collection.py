from abc import ABC, abstractmethod

from .service_entry import ServiceEntry


class IServiceEntryCollection(ABC):
    @abstractmethod
    def get[T](self, interface: type[T]) -> ServiceEntry[T]: ...

    @abstractmethod
    def set[T](self, interface: type[T], entry: ServiceEntry[T]) -> None: ...

    @abstractmethod
    def remove[T](self, key: type[T]) -> None: ...

    @abstractmethod
    def __contains__(self, key: type) -> bool: ...