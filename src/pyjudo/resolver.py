import inspect
import logging
import threading
from typing import Any, Callable, cast, get_args, get_origin, override


from pyjudo.core import IResolver, IServiceEntryCollection, IServiceCache, IScopeStack, ServiceLife
from pyjudo.exceptions import (
    ServiceCircularDependencyError,
    ServiceResolutionError,
    ServiceScopeError,
)
from pyjudo.factory import Factory, FactoryProxy


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
    def resolve_anonymous[T](self, constructor: Callable[..., T], overrides: dict[str, Any], binding: Any | None = None) -> T:
        return self._create_instance(constructor, overrides, binding)

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
        elif overrides: # already exists and overrides are specified
            raise ServiceResolutionError(
                f"Singleton service '{interface.__name__}' already exists. Cannot specify overrides."
            )
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
        self, constructor: type[T] | Callable[..., T], overrides: dict[str, Any], binding: Any | None = None
    ) -> T:
        if inspect.isclass(constructor):
            signature = inspect.signature(constructor.__init__)
            parameters = list(signature.parameters.values())[1:] # Skip 'self'
        else:
            signature = inspect.signature(constructor)
            parameters = list(signature.parameters.values())

        constructor_args: list[Any] = []
        constructor_kwargs: dict[str, Any] = {}

        for param in parameters:
            name = param.name

            if name in ("self", "cls") and binding is not None:
                constructor_args.insert(0, binding)
                continue

            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue # Skip *args and **kwargs

            origin = get_origin(param.annotation)
            args = get_args(param.annotation)

            if origin is Factory and args:
                interface = args[0]
                resolved = FactoryProxy(self, interface)
            elif name in overrides:
                resolved = overrides[name]
            elif param.annotation in self.service_entry_collection:
                resolved = self.resolve(param.annotation, {})
            elif param.default != inspect.Parameter.empty:
                resolved = param.default
            else:
                raise ServiceResolutionError(
                    f"Unable to resolve dependency '{name}' for '{constructor.__name__}'"
                )
            
            if param.kind == inspect.Parameter.POSITIONAL_ONLY:
                constructor_args.append(resolved)
            elif param.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY):
                constructor_kwargs[name] = resolved
            else:
                raise Exception("Invalid parameter kind: {param.kind}")
        
        return cast(T, constructor(*constructor_args, **constructor_kwargs))


    def _create_instance__[T](
        self, constructor: type[T] | Callable[..., T], overrides: dict[str, Any], instance: Any | None = None
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