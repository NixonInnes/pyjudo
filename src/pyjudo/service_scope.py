from functools import partial
import logging
from typing import Any, Callable, TYPE_CHECKING

from pyjudo.disposable import Disposable

if TYPE_CHECKING:
    from pyjudo.service_container import ServiceContainer


class ServiceScope:
    """
    Represents a scope for services.
    """
    def __init__(self, service_container: "ServiceContainer") -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)
        self._instances: dict[type[Any], Any] = {}
        self._disposables: list[Disposable] = []
        self._container: "ServiceContainer" = service_container
    
    def get[T](self, abstract_class: type[T], **overrides: Any) -> T:
        return self._container._resolve(abstract_class, scope=self, **overrides)

    def has_instance(self, abstract_class: type) -> bool:
        return abstract_class in self._instances
    
    def get_instance[T](self, abstract_class: type[T]) -> T:
        return self._instances[abstract_class]

    def set_instance(self, abstract_class: type, instance: Any) -> None:
        self._instances[abstract_class] = instance
        if isinstance(instance, Disposable):
            self._disposables.append(instance)
    
    def __enter__(self):
        self._container._push_scope(self)
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        for instance in self._disposables:
            instance.dispose()
        self._container._pop_scope()

    def __getitem__[T](self, key: type[T]) -> Callable[..., T]:
        return partial(self.get, key)