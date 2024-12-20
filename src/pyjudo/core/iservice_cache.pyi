"""
This type stub file was generated by pyright.
"""

from abc import ABC, abstractmethod

class IServiceCache(ABC):
    @abstractmethod
    def get[T](self, interface: type[T]) -> T | None:
        ...
    
    @abstractmethod
    def add[T](self, interface: type[T], instance: T) -> None:
        ...
    


