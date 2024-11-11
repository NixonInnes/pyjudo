import logging
from typing import override, Any, Callable, Self

from pyjudo.core import IServiceContainer, IServiceEntryCollection, IServiceCache, IServiceScope, IScopeStack, IResolver
from pyjudo.service_entry import ServiceEntry
from pyjudo.service_life import ServiceLife


class ServiceContainer(IServiceContainer):
    def __init__(
        self,
        service_entry_collection: IServiceEntryCollection,
        singleton_cache: IServiceCache,
        scope_stack: IScopeStack,
        scope_factory: Callable[[IScopeStack, IResolver], IServiceScope],
        resolver: IResolver,
    ) -> None:
        self._logger = logging.getLogger(self.__class__.__name__)

        self.service_entry_collection = service_entry_collection
        self.singleton_cache = singleton_cache
        self.scope_stack = scope_stack
        self.scope_factory = scope_factory
        self.resolver = resolver

    @override
    def register[T](
        self,
        interface: type[T],
        constructor: type[T] | Callable[..., T],
        lifetime: ServiceLife = ServiceLife.TRANSIENT,
    ) -> None:
        entry = ServiceEntry(constructor, lifetime)
        self.service_entry_collection.set(interface, entry)

    @override
    def unregister(self, interface: type) -> None:
        self.service_entry_collection.remove(interface)

    @override
    def add_transient[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> Self:
        self.register(interface, constructor, ServiceLife.TRANSIENT)
        return self

    @override
    def add_scoped[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> Self:
        self.register(interface, constructor, ServiceLife.SCOPED)
        return self

    @override
    def add_singleton[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> Self:
        self.register(interface, constructor, ServiceLife.SINGLETON)
        return self

    @override
    def get[T](self, interface: type[T], **overrides: Any) -> T:
        return self.resolver.resolve(interface, overrides)

    @override
    def is_registered(self, interface: type) -> bool:
        return interface in self.service_entry_collection

    @override
    def create_scope(self) -> IServiceScope:
        return self.scope_factory(self.scope_stack, self.resolver)