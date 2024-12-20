"""
This type stub file was generated by pyright.
"""

from typing import Any, Protocol, override
from pyjudo.core import IResolver

class Factory[T](Protocol):
    def __call__(self, **overrides: Any) -> T:
        ...
    


class FactoryProxy[T](Factory[T]):
    """
    A proxy for a factory that resolves an interface.
    Calling the proxy will resolve the interface from the container.
    """
    _resolver: IResolver
    _interface: type[T]
    def __init__(self, resolver: IResolver, interface: type[T]) -> None:
        ...
    
    @override
    def __call__(self, **overrides: Any) -> T:
        ...
    
    @override
    def __repr__(self) -> str:
        ...
    


