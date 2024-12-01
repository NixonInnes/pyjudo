"""
This type stub file was generated by pyright.
"""

from typing import override
from pyjudo.core import IServiceEntryCollection, ServiceEntry

class ServiceEntryCollection(IServiceEntryCollection):
    def __init__(self) -> None:
        ...
    
    @override
    def get[T](self, interface: type[T]) -> ServiceEntry[T]:
        ...
    
    @override
    def set[T](self, interface: type[T], entry: ServiceEntry[T]) -> None:
        ...
    
    @override
    def remove[T](self, key: type[T]) -> None:
        ...
    
    @override
    def __contains__(self, key: type) -> bool:
        ...
    

