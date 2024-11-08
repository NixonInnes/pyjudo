from typing import Any, Protocol

from pyjudo.iservice_container import IServiceContainer


class Factory[T](Protocol):
    def __call__(self, **overrides: Any) -> T: ...


class FactoryProxy[T](Factory[T]):
    _container: IServiceContainer
    _abstract_class: type[T]

    def __init__(self, container: IServiceContainer, abstract_class: type[T]):
        self._container = container
        self._abstract_class = abstract_class

    def __call__(self, **overrides: Any) -> T:
        return self._container.get(self._abstract_class, **overrides)

    def __repr__(self) -> str:
        return f"FactoryProxy({self._abstract_class.__name__})"