"""
This type stub file was generated by pyright.
"""

from typing import Any, override
from pyjudo.core import IServiceCache

class ServiceCache(IServiceCache):
    def __init__(self, initial: dict[type[Any], Any] | None = ...) -> None:
        ...
    
    @override
    def get[T](self, interface: type[T]) -> T | None:
        ...
    
    @override
    def add[T](self, interface: type[T], instance: T) -> None:
        ...
    


