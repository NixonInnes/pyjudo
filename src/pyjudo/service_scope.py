from functools import partial
import logging
from typing import override, Any, Callable

from pyjudo.core import IServiceScope, IScopeStack, IResolver, IServiceCache
from pyjudo.disposable import Disposable


class ServiceScope(IServiceScope):
    """
    Represents a scope for services.
    """

    def __init__(self, cache: IServiceCache, stack: IScopeStack, resolver: IResolver) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)

        self.cache: IServiceCache = cache
        self.stack: IScopeStack = stack
        self.resolver: IResolver = resolver
        self.disposables: list[Disposable] = []

    @override
    def get[T](self, interface: type[T], **overrides: Any) -> T:
        return self.resolver.resolve(interface, overrides)

    @override
    def get_instance[T](self, interface: type[T]) -> T | None:
        return self.cache.get(interface)

    @override
    def add_instance[T](self, interface: type[T], instance: T) -> None:
        self.cache.add(interface, instance)
        if isinstance(instance, Disposable):
            self.disposables.append(instance)

    @override
    def __getitem__[T](self, key: type[T]) -> Callable[..., T]:
        return partial(self.get, key)

    @override
    def __enter__(self):
        self.stack.push(self)  # Use container's scope_stack
        return self

    @override
    def __exit__(self, _exc_type, _exc_value, _traceback):
        for disposable in self.disposables:
            disposable.dispose()
        self.stack.pop()