from pyjudo.core import IResolver, IServiceContainer, IScopeStack, IServiceScope, ServiceLife

from .factory import Factory
from .resolver import Resolver
from .scope_stack import ScopeStack
from .service_cache import ServiceCache
from .service_container import ServiceContainer as ServiceContainerBase
from .service_entry_collection import ServiceEntryCollection
from .service_scope import ServiceScope


def ServiceContainer() -> ServiceContainerBase:
    def _scope_factory(stack: IScopeStack, resolver: IResolver) -> IServiceScope:
        cache = ServiceCache()
        return ServiceScope(cache, stack, resolver)

    service_entry_collection = ServiceEntryCollection()
    singleton_cache = ServiceCache()
    scope_stack = ScopeStack()
    resolver = Resolver(
        service_entry_collection=service_entry_collection,
        singleton_cache=singleton_cache,
        scope_stack=scope_stack,
    )
    
    return ServiceContainerBase(
        service_entry_collection=service_entry_collection,
        singleton_cache=singleton_cache,
        scope_stack=scope_stack,
        scope_factory=_scope_factory,
        resolver=resolver,
    )

__all__ = [
    "Factory",
    "ServiceContainer",
    "IServiceContainer",
    "ServiceLife",
]

