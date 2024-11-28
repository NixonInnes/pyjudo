from typing import override, Any, Protocol

from pyjudo.core import IResolver


class Factory[T](Protocol):
    def __call__(self, **overrides: Any) -> T: ...


class FactoryProxy[T](Factory[T]):
    """
    A proxy for a factory that resolves an interface.
    Calling the proxy will resolve the interface from the container.
    """
    _resolver: IResolver
    _interface: type[T]

    def __init__(self, resolver: IResolver, interface: type[T]):
        self._resolver = resolver
        self._interface = interface

    @override
    def __call__(self, **overrides: Any) -> T:
        return self._resolver.resolve(self._interface, overrides)

    @override
    def __repr__(self) -> str:
        return f"FactoryProxy({self._interface.__name__})"