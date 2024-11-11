from abc import ABC, abstractmethod
import logging
import inspect
import threading
from typing import Any, Callable, Protocol, cast, get_args, get_origin, override, Self
from functools import partial

from pyjudo.exceptions import (
    ServiceCircularDependencyError,
    ServiceResolutionError,
    ServiceRegistrationError,
    ServiceTypeError,
    ServiceScopeError,
)
from pyjudo.disposable import Disposable
from pyjudo.service_life import ServiceLife


class ServiceEntry[T]:
    """
    Represents a service entry in the container.
    """

    constructor: type[T] | Callable[..., T]
    lifetime: ServiceLife

    def __init__(self, constructor: type[T] | Callable[..., T], lifetime: ServiceLife):
        self.constructor = constructor
        self.lifetime = lifetime


class IResolver(ABC):
    @abstractmethod
    def resolve[T](self, interface: type[T], overrides: dict[str, Any]) -> T: ...


class IServiceCache(ABC):
    @abstractmethod
    def get[T](self, interface: type[T]) -> T | None: ...

    @abstractmethod
    def add[T](self, interface: type[T], instance: T) -> None: ...

    @abstractmethod
    def __or__(self, other: Self | dict[type[Any], Any]) -> Self: ...

    @abstractmethod
    def __contains__(self, key: type) -> bool: ...


class IServiceRegistrar(ABC):
    @abstractmethod
    def register[T](
        self,
        interface: type[T],
        constructor: type[T] | Callable[..., T],
        lifetime: ServiceLife = ServiceLife.TRANSIENT,
    ) -> None: ...

    @abstractmethod
    def unregister(self, interface: type) -> None: ...

    @abstractmethod
    def is_registered(self, interface: type) -> bool: ...

    @abstractmethod
    def add_transient[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> None: ...

    @abstractmethod
    def add_scoped[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> None: ...

    @abstractmethod
    def add_singleton[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> None: ...


class IServiceEntryCollection(ABC):
    @abstractmethod
    def get[T](self, interface: type[T]) -> ServiceEntry[T]: ...

    @abstractmethod
    def set[T](self, interface: type[T], entry: ServiceEntry[T]) -> None: ...

    @abstractmethod
    def remove[T](self, key: type[T]) -> None: ...

    @abstractmethod
    def __contains__(self, key: type) -> bool: ...


class IServiceScope(ABC):
    @abstractmethod
    def get[T](self, interface: type[T], **overrides: Any) -> T: ...

    @abstractmethod
    def get_instance[T](self, interface: type[T]) -> T | None: ...

    @abstractmethod
    def add_instance[T](self, interface: type[T], instance: T) -> None: ...

    @abstractmethod
    def __getitem__[T](self, key: type[T]) -> Callable[..., T]: ...

    @abstractmethod
    def __enter__(self) -> Self: ...

    @abstractmethod
    def __exit__(self, exc_type, exc_value, traceback) -> None: ...


class IScopeStack(ABC):
    @abstractmethod
    def push(self, scope: IServiceScope) -> None: ...

    @abstractmethod
    def pop(self) -> None: ...

    @abstractmethod
    def get_current(self) -> IServiceScope | None: ...


class ServiceEntryCollection(IServiceEntryCollection):
    def __init__(self):
        self._entries: dict[type[Any], ServiceEntry[Any]] = {}

    @override
    def get[T](self, interface: type[T]) -> ServiceEntry[T]:
        entry = self._entries.get(interface)
        if entry is None:
            raise ServiceResolutionError(
                f"No service registered for: {interface.__name__}"
            )
        return entry

    @override
    def set[T](self, interface: type[T], entry: ServiceEntry[T]) -> None:
        if interface in self._entries:
            raise ServiceRegistrationError(
                f"Service '{interface.__name__}' is already registered."
            )
        self._entries[interface] = entry

    @override
    def remove[T](self, key: type[T]) -> None:
        _ = self._entries.pop(key, None)

    @override
    def __contains__(self, key: type) -> bool:
        return key in self._entries


class ServiceCache(IServiceCache):
    def __init__(self, initial: dict[type[Any], Any] | None = None):
        self._cache: dict[type[Any], Any] = initial or {}

    def get[T](self, interface: type[T]) -> T | None:
        return self._cache.get(interface)

    def add[T](self, interface: type[T], instance: T) -> None:
        self._cache[interface] = instance

    def __or__(self, other: Self | dict[type[Any], Any]) -> Self:
        if isinstance(other, ServiceCache):
            return self.__class__(self._cache | other._cache)
        return self.__class__(self._cache | other)

    def __contains__(self, key: type) -> bool:
        return key in self._cache


class ScopeStack(IScopeStack):
    def __init__(self):
        self.__scopes_stack = threading.local()
        self.__lock = threading.Lock()
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @property
    def _scope_stack(self) -> list[IServiceScope]:
        if not hasattr(self.__scopes_stack, "scopes"):
            self.__scopes_stack.scopes = []
        return self.__scopes_stack.scopes

    @override
    def get_current(self) -> IServiceScope | None:
        with self.__lock:
            if not self._scope_stack:
                return None
            return self._scope_stack[-1]

    @override
    def push(self, scope: IServiceScope) -> None:
        with self.__lock:
            self._scope_stack.append(scope)
            self._logger.debug("Pushed new scope to stack.")

    @override
    def pop(self) -> None:
        with self.__lock:
            try:
                _ = self._scope_stack.pop()
                self._logger.debug("Popped scope from stack.")
            except IndexError:
                raise ServiceScopeError("No scope available to pop.")


class ServiceScope(IServiceScope):
    """
    Represents a scope for services.
    """

    def __init__(self, stack: IScopeStack, resolver: IResolver) -> None:
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)

        self.cache: IServiceCache = ServiceCache()
        self.disposables: list[Disposable] = []
        self.stack: IScopeStack = stack
        self.resolver: IResolver = resolver

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
    def __exit__(self, exc_type, exc_value, traceback):
        for disposable in self.disposables:
            disposable.dispose()
        self.stack.pop()


class Factory[T](Protocol):
    def __call__(self, **overrides: Any) -> T: ...


class FactoryProxy[T](Factory[T]):
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


class Resolver(IResolver):
    def __init__(
        self,
        service_entry_collection: IServiceEntryCollection,
        singleton_cache: IServiceCache,
        scope_stack: IScopeStack,
    ) -> None:
        self.__resolution_stack = threading.local()
        self._logger: logging.Logger = logging.getLogger(self.__class__.__name__)

        self.service_entry_collection = service_entry_collection
        self.singleton_cache = singleton_cache
        self.scope_stack = scope_stack

    @property
    def _resolution_stack(self) -> set[type]:
        if not hasattr(self.__resolution_stack, "stack"):
            self.__resolution_stack.stack = set()
            self._logger.debug("Initialized a new resolution stack for the thread.")
        return self.__resolution_stack.stack

    @override
    def resolve[T](self, interface: type[T], overrides: dict[str, Any]) -> T:
        if interface in self._resolution_stack:
            raise ServiceCircularDependencyError(
                f"Circular dependency detected for '{interface.__name__}'"
            )

        _ = self._resolution_stack.add(interface)
        self._logger.debug(f"Resolving service '{interface.__name__}'")

        try:
            entry = self.service_entry_collection.get(interface)

            match entry.lifetime:
                case ServiceLife.SINGLETON:
                    return self._get_singleton(interface, entry.constructor, overrides)
                case ServiceLife.SCOPED:
                    return self._get_scoped(interface, entry.constructor, overrides)
                case ServiceLife.TRANSIENT:
                    return self._get_transient(interface, entry.constructor, overrides)
        finally:
            self._resolution_stack.remove(interface)

    def _get_singleton[T](
        self,
        interface: type[T],
        constructor: type[T] | Callable[..., T],
        overrides: dict[str, Any],
    ) -> T:
        instance = self.singleton_cache.get(interface)

        if instance is None:
            instance = self._create_instance(constructor, overrides)
            self.singleton_cache.add(interface, instance)
        return instance

    def _get_scoped[T](
        self,
        interface: type[T],
        constructor: type[T] | Callable[..., T],
        overrides: dict[str, Any],
    ) -> T:
        scope = self.scope_stack.get_current()

        if scope is None:
            raise ServiceScopeError("No scope available to resolve scoped services.")

        instance = scope.get_instance(interface)

        if instance is None:
            instance = self._create_instance(constructor, overrides)
            scope.add_instance(interface, instance)
        return instance

    def _get_transient[T](
        self,
        _interface: type[T],
        constructor: type[T] | Callable[..., T],
        overrides: dict[str, Any],
    ) -> T:
        return self._create_instance(constructor, overrides)

    def _create_instance[T](
        self, constructor: type[T] | Callable[..., T], overrides: dict[str, Any]
    ) -> T:
        if inspect.isclass(constructor):
            type_hints = inspect.signature(constructor.__init__).parameters
        else:
            type_hints = inspect.signature(constructor).parameters

        kwargs = {}

        for name, param in type_hints.items():
            if name == "self":
                continue

            # Skip *args and **kwargs
            if param.kind in (
                inspect.Parameter.VAR_POSITIONAL,
                inspect.Parameter.VAR_KEYWORD,
            ):
                continue

            origin = get_origin(param.annotation)
            args = get_args(param.annotation)
            if origin is Factory and args:
                interface = args[0]
                kwargs[name] = FactoryProxy(self, interface)
                continue

            if name in overrides:
                kwargs[name] = overrides[name]
            elif param.annotation in self.service_entry_collection:
                kwargs[name] = self.resolve(param.annotation, {})
            elif param.default != inspect.Parameter.empty:
                kwargs[name] = param.default
            else:
                raise ServiceResolutionError(
                    f"Unable to resolve dependency '{name}' for '{constructor.__name__}'"
                )

        self._logger.debug(f"Creating new instance of '{T}'")

        return cast(T, constructor(**kwargs))  # TODO: Remove cast


class IServiceContainer(ABC):
    singleton_cache: IServiceCache
    scope_stack: IScopeStack
    service_entry_collection: IServiceEntryCollection
    resolver: IResolver

    @abstractmethod
    def register[T](
        self,
        interface: type[T],
        constructor: type[T] | Callable[..., T],
        lifetime: ServiceLife = ServiceLife.TRANSIENT,
    ) -> None: ...

    @abstractmethod
    def unregister(self, interface: type) -> None: ...

    @abstractmethod
    def add_transient[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> Self: ...

    @abstractmethod
    def add_scoped[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> Self: ...

    @abstractmethod
    def add_singleton[T](
        self, interface: type[T], constructor: type[T] | Callable[..., T]
    ) -> Self: ...

    @abstractmethod
    def get[T](self, interface: type[T], **overrides: Any) -> T: ...

    @abstractmethod
    def is_registered(self, interface: type) -> bool: ...

    @abstractmethod
    def create_scope(self) -> IServiceScope: ...

    def __getitem__[T](self, key: type[T]) -> Callable[..., T]:
        return partial(self.get, key)


class ServiceContainer(IServiceContainer):
    def __init__(self):
        self.singleton_cache = ServiceCache()
        self.scope_stack = ScopeStack()
        self.service_entry_collection = ServiceEntryCollection()
        self.resolver = Resolver(
            service_entry_collection=self.service_entry_collection,
            singleton_cache=self.singleton_cache,
            scope_stack=self.scope_stack,
        )

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
    def create_scope(self) -> ServiceScope:
        return ServiceScope(stack=self.scope_stack, resolver=self.resolver)
