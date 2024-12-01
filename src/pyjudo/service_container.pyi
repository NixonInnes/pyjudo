"""
This type stub file was generated by pyright.
"""

from typing import Any, Callable, Self, override
from pyjudo.core import IResolver, IScopeStack, IServiceCache, IServiceContainer, IServiceEntryCollection, IServiceScope, ServiceLife

class InjectDecorator:
    def __init__(self, resolver: IResolver, func: Callable[..., Any]) -> None:
        ...
    
    def __get__[T](self, instance: T | None, owner: type[T] | None) -> Callable[..., Any]:
        ...
    
    @property
    def __name__(self) -> str:
        ...
    
    def __call__(self, *args, **kwargs): # -> Any:
        ...
    


class ServiceContainer(IServiceContainer):
    def __init__(self, service_entry_collection: IServiceEntryCollection, singleton_cache: IServiceCache, scope_stack: IScopeStack, scope_factory: Callable[[IScopeStack, IResolver], IServiceScope], resolver: IResolver) -> None:
        ...
    
    @override
    def register[T](self, interface: type[T], constructor: type[T] | Callable[..., T], lifetime: ServiceLife = ...) -> None:
        ...
    
    def inject(self, func: Callable[..., Any]) -> Callable[..., Any]:
        ...
    
    @override
    def unregister(self, interface: type) -> None:
        ...
    
    @override
    def add_transient[T](self, interface: type[T], constructor: type[T] | Callable[..., T]) -> Self:
        ...
    
    @override
    def add_scoped[T](self, interface: type[T], constructor: type[T] | Callable[..., T]) -> Self:
        ...
    
    @override
    def add_singleton[T](self, interface: type[T], constructor: type[T] | Callable[..., T]) -> Self:
        ...
    
    @override
    def get[T](self, interface: type[T], **overrides: Any) -> T:
        ...
    
    @override
    def get_factory[T](self, interface: type[T]) -> Callable[..., T]:
        ...
    
    @override
    def is_registered(self, interface: type) -> bool:
        ...
    
    @override
    def create_scope(self) -> IServiceScope:
        ...
    


