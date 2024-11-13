from functools import wraps
import inspect
import logging
import threading
from typing import TypeAlias, override, Any, Callable, Self, Union

from pyjudo.core import (
    IServiceContainer,
    IServiceEntryCollection,
    IServiceCache,
    IServiceScope,
    IScopeStack,
    IResolver,
    ServiceLife,
    ServiceEntry,
)
from pyjudo.exceptions import ServiceRegistrationError, ServiceResolutionError, ServiceTypeError
from pyjudo.factory import FactoryProxy


class InjectDecorator:
    def __init__(self, resolver: IResolver, func: Callable[..., Any]) -> None:
        self.resolver: IResolver = resolver
        self.func: Callable[..., Any] = func
    
    def __get__[T](self, instance: T | None, owner: type[T] | None) -> Callable[..., Any]:
        if isinstance(self.func, classmethod):
            original_func = self.func.__func__

            @wraps(original_func)
            def classmethod_wrapper(*args: Any, **kwargs: Any) -> Any:
                return self.resolver.resolve_anonymous(original_func, kwargs, binding=owner)
            return classmethod_wrapper

        elif isinstance(self.func, staticmethod):
            original_func = self.func.__func__

            @wraps(original_func)
            def staticmethod_wrapper(*args: Any, **kwargs: Any) -> Any:
                return self.resolver.resolve_anonymous(original_func, kwargs, binding=None)
            return staticmethod_wrapper

        else:
            @wraps(self.func)
            def bound_wrapper(*args: Any, **kwargs: Any) -> Any:
                return self.resolver.resolve_anonymous(self.func, kwargs, binding=instance)
            return bound_wrapper

    def __call__(self, *args, **kwargs):
        return self.resolver.resolve_anonymous(self.func, kwargs)


class ServiceContainer(IServiceContainer):
    def __init__(
        self,
        service_entry_collection: IServiceEntryCollection,
        singleton_cache: IServiceCache,
        scope_stack: IScopeStack,
        scope_factory: Callable[[IScopeStack, IResolver], IServiceScope],
        resolver: IResolver,
    ) -> None:
        self.__lock = threading.Lock()
        self._logger = logging.getLogger(self.__class__.__name__)

        self.service_entry_collection = service_entry_collection
        self.singleton_cache = singleton_cache
        self.scope_stack = scope_stack
        self.scope_factory = scope_factory
        self.resolver = resolver

        self.register(IServiceContainer, self.__class__, ServiceLife.SINGLETON)
        self.singleton_cache.add(IServiceContainer, self)

    @override
    def register[T](
        self,
        interface: type[T],
        constructor: type[T] | Callable[..., T],
        lifetime: ServiceLife = ServiceLife.TRANSIENT,
    ) -> None:
        if inspect.isclass(constructor):
            if not issubclass(constructor, interface):
                raise ServiceRegistrationError(f"'{constructor.__name__}' does not implement '{interface.__name__}'")
        elif callable(constructor):
            return_annotation = inspect.signature(constructor).return_annotation

            if return_annotation is inspect.Signature.empty:
                raise ServiceRegistrationError(f"Callable '{constructor.__name__}' must have a return annotation.")
            
            if not issubclass(return_annotation, interface):
                raise ServiceRegistrationError(f"'{constructor.__name__}' does not return '{interface.__name__}'")
        else:
            raise ServiceRegistrationError("Constructor must be a class or callable")

        with self.__lock:
            entry = ServiceEntry(constructor, lifetime)
            self.service_entry_collection.set(interface, entry)

    def inject(self, func: Callable[..., Any]) -> Callable[..., Any]:
        return InjectDecorator(self.resolver, func)

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
        with self.__lock:
            service = self.resolver.resolve(interface, overrides)
        if not issubclass(type(service), interface):
            raise ServiceTypeError(f"Service '{service}' is not of type '{interface.__name__}'")
        return service

    @override
    def get_factory[T](self, interface: type[T]) -> Callable[..., T]:
        if not self.is_registered(interface):
            raise ServiceResolutionError(f"Service '{interface.__name__}' is not registered.")
        return FactoryProxy(self.resolver, interface)

    @override
    def is_registered(self, interface: type) -> bool:
        return interface in self.service_entry_collection

    @override
    def create_scope(self) -> IServiceScope:
        return self.scope_factory(self.scope_stack, self.resolver)
