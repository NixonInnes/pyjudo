import inspect
from typing import Any, Callable, Protocol, runtime_checkable
import unittest
from unittest.mock import MagicMock, Mock, patch

from pyjudo.core import (
    IServiceEntryCollection,
    IServiceCache,
    IServiceScope,
    IScopeStack,
    ServiceLife,
)
from pyjudo.exceptions import ServiceCircularDependencyError, ServiceResolutionError, ServiceScopeError
from pyjudo.factory import Factory, FactoryProxy
from pyjudo.resolver import Resolver

@runtime_checkable
class IServiceA(Protocol):
    pass


class ServiceA(IServiceA):
    pass


@runtime_checkable
class IServiceB(Protocol):
    pass


class ServiceB(IServiceB):
    def __init__(self, service_a: IServiceA):
        self.service_a = service_a

class Test_Resolver(unittest.TestCase):
    def setUp(self):
        self.mock_service_entry_collection: IServiceEntryCollection = MagicMock(spec=IServiceEntryCollection) # pyright: ignore[reportUninitializedInstanceVariable]
        self.mock_service_cache: IServiceCache = Mock(spec=IServiceCache) # pyright: ignore[reportUninitializedInstanceVariable]
        self.mock_service_scope_stack: IScopeStack = Mock(spec=IScopeStack) # pyright: ignore[reportUninitializedInstanceVariable]

        self.resolver: Resolver = Resolver( # pyright: ignore[reportUninitializedInstanceVariable]
            self.mock_service_entry_collection,
            self.mock_service_cache,
            self.mock_service_scope_stack,
        )

    def test_resolution_stack_initialisation(self):
        stack = self.resolver._resolution_stack
        self.assertEqual(stack, set())

    def test_resolve_anonymous(self):
        constructor = Mock(return_value="instance")
        instance = self.resolver.resolve_anonymous(constructor, {})

        self.assertEqual(instance, "instance")

    def test_resolve_singleton(self):
        interface = Mock()
        entry = Mock()
        entry.lifetime = ServiceLife.SINGLETON
        entry.constructor = Mock(return_value="singleton_instance")
        self.mock_service_entry_collection.get.return_value = entry

        # Simulate instance not cached
        self.mock_service_cache.get.return_value = None

        instance = self.resolver.resolve(interface, {})

        self.assertEqual(instance, "singleton_instance")
        self.mock_service_cache.add.assert_called_once()

    def test_resolve_singleton_cached(self):
        interface = Mock()
        entry = Mock()
        entry.lifetime = ServiceLife.SINGLETON
        entry.constructor = Mock(return_value="singleton_instance")
        self.mock_service_entry_collection.get.return_value = entry

        # Simulate instance cached
        self.mock_service_cache.get.return_value = "cached_instance"

        instance = self.resolver.resolve(interface, {})

        self.assertEqual(instance, "cached_instance")
        self.mock_service_cache.add.assert_not_called()

    def test_resolve_scoped(self):
        interface = Mock()
        entry = Mock()
        entry.lifetime = ServiceLife.SCOPED
        entry.constructor = Mock(return_value="scoped_instance")
        self.mock_service_entry_collection.get.return_value = entry
        
        # Simulate instance not cached
        current_scope = Mock(spec=IServiceScope)
        current_scope.get_instance.return_value = None

        self.mock_service_scope_stack.get_current.return_value = current_scope

        instance = self.resolver.resolve(interface, {})

        self.assertEqual(instance, "scoped_instance")
        current_scope.add_instance.assert_called_once()

    def test_resolve_scoped_cached(self):
        interface = Mock()
        entry = Mock()
        entry.lifetime = ServiceLife.SCOPED
        entry.constructor = Mock(return_value="scoped_instance")
        self.mock_service_entry_collection.get.return_value = entry

        current_scope = Mock(spec=IServiceScope)
        current_scope.get_instance.return_value = "cached_instance"

        self.mock_service_scope_stack.get_current.return_value = current_scope

        instance = self.resolver.resolve(interface, {})

        self.assertEqual(instance, "cached_instance")
        current_scope.add_instance.assert_not_called()

    def test_resolve_transient(self):
        interface = Mock()
        entry = Mock()
        entry.lifetime = ServiceLife.TRANSIENT
        entry.constructor = Mock(return_value="transient_instance")
        self.mock_service_entry_collection.get.return_value = entry

        instance = self.resolver.resolve(interface, {})

        self.assertEqual(instance, "transient_instance")

    def test_circular_dependency(self):
        interface = Mock()

        self.resolver._resolution_stack.add(interface)

        with self.assertRaises(ServiceCircularDependencyError):
            self.resolver.resolve(interface, {})

    def test_no_scope_error(self):
        interface = Mock()
        entry = Mock()
        entry.lifetime = ServiceLife.SCOPED
        self.mock_service_entry_collection.get.return_value = entry

        self.mock_service_scope_stack.get_current.return_value = None

        with self.assertRaises(ServiceScopeError):
            self.resolver.resolve(interface, {})

    def test_singleton_overrides_error(self):
        interface = Mock()
        entry = Mock()
        entry.lifetime = ServiceLife.SINGLETON
        self.mock_service_entry_collection.get.return_value = entry

        self.mock_service_cache.get.return_value = "cached_instance"

        with self.assertRaises(ServiceResolutionError):
            self.resolver.resolve(interface, {"override": "value"})

    def test_create_instance_with_callable_constructor(self):
        # Test when constructor is a function
        def constructor(service_a: IServiceA):
            return ServiceB(service_a)

        self.mock_service_entry_collection.__contains__.side_effect = lambda x: x == IServiceA
        self.mock_service_entry_collection.get.return_value = Mock(
            constructor=ServiceA, lifetime=ServiceLife.TRANSIENT
        )
        service_instance = self.resolver._create_instance(constructor, overrides={})
        self.assertIsInstance(service_instance, ServiceB)
        self.assertIsInstance(service_instance.service_a, ServiceA)

    def test_create_instance_with_positional_only_parameter(self):
        # Test with positional-only parameters (Python 3.8+)
        def constructor(service_a: IServiceA, /):
            return ServiceB(service_a)

        self.mock_service_entry_collection.__contains__.side_effect = lambda x: x == IServiceA
        self.mock_service_entry_collection.get.return_value = Mock(
            constructor=ServiceA, lifetime=ServiceLife.TRANSIENT
        )
        service_instance = self.resolver._create_instance(constructor, overrides={})
        self.assertIsInstance(service_instance, ServiceB)

    def test_create_instance_with_keyword_only_parameter(self):
        # Test with keyword-only parameters
        def constructor(*, service_a: IServiceA):
            return ServiceB(service_a)

        self.mock_service_entry_collection.__contains__.side_effect = lambda x: x == IServiceA
        self.mock_service_entry_collection.get.return_value = Mock(
            constructor=ServiceA, lifetime=ServiceLife.TRANSIENT
        )
        service_instance = self.resolver._create_instance(constructor, overrides={})
        self.assertIsInstance(service_instance, ServiceB)

    def test_create_instance_with_var_positional_parameters(self):
        # Test that *args are skipped
        def constructor(*args, service_a: IServiceA):
            return ServiceB(service_a)

        self.mock_service_entry_collection.__contains__.side_effect = lambda x: x == IServiceA
        self.mock_service_entry_collection.get.return_value = Mock(
            constructor=ServiceA, lifetime=ServiceLife.TRANSIENT
        )
        service_instance = self.resolver._create_instance(constructor, overrides={})
        self.assertIsInstance(service_instance, ServiceB)

    def test_create_instance_with_var_keyword_parameters(self):
        # Test that **kwargs are skipped
        def constructor(service_a: IServiceA, **kwargs):
            return ServiceB(service_a)

        self.mock_service_entry_collection.__contains__.side_effect = lambda x: x == IServiceA
        self.mock_service_entry_collection.get.return_value = Mock(
            constructor=ServiceA, lifetime=ServiceLife.TRANSIENT
        )
        service_instance = self.resolver._create_instance(constructor, overrides={})
        self.assertIsInstance(service_instance, ServiceB)

    def test_create_instance_with_factory_annotation(self):
        # Test parameters annotated with Factory[Interface]
        class ServiceC:
            def __init__(self, factory: Factory[IServiceA]):
                self.factory = factory

        service_instance = self.resolver._create_instance(ServiceC, overrides={})
        self.assertIsInstance(service_instance, ServiceC)
        self.assertIsInstance(service_instance.factory, FactoryProxy)

    def test_create_instance_with_overrides(self):
        # Test when parameter name is in overrides
        def constructor(service_a: IServiceA):
            return ServiceB(service_a)

        override_service = ServiceA()
        service_instance = self.resolver._create_instance(constructor, overrides={'service_a': override_service})
        self.assertIsInstance(service_instance, ServiceB)
        self.assertEqual(service_instance.service_a, override_service)

    def test_create_instance_with_default_parameter(self):
        # Test parameter has default value
        def constructor(service_a: IServiceA = ServiceA()):
            return ServiceB(service_a)

        service_instance = self.resolver._create_instance(constructor, overrides={})
        self.assertIsInstance(service_instance, ServiceB)
        self.assertIsInstance(service_instance.service_a, ServiceA)

    def test_create_instance_unresolvable_parameter_raises_error(self):
        # Test when parameter cannot be resolved
        def constructor(service_a: IServiceA):
            return ServiceB(service_a)

        self.mock_service_entry_collection.__contains__.return_value = False
        with self.assertRaises(ServiceResolutionError):
            self.resolver._create_instance(constructor, overrides={})

    def test_create_instance_with_binding_self(self):
        # Test handling 'self' when binding is provided
        class ServiceD:
            def method(self, service_a: IServiceA):
                return service_a

        instance = ServiceD()
        self.mock_service_entry_collection.__contains__.side_effect = lambda x: x == IServiceA
        self.mock_service_entry_collection.get.return_value = Mock(
            constructor=ServiceA, lifetime=ServiceLife.TRANSIENT
        )

        bound_method = instance.method
        service_instance = self.resolver._create_instance(bound_method, overrides={}, binding=instance)
        self.assertIsInstance(service_instance, ServiceA)

    def test_create_instance_constructor_is_class(self):
        # Test when constructor is a class
        self.mock_service_entry_collection.__contains__.side_effect = lambda x: False
        service_instance = self.resolver._create_instance(ServiceA, overrides={})
        self.assertIsInstance(service_instance, ServiceA)

    def test_create_instance_constructor_with_cls_binding(self):
        # Test handling 'cls' when binding is provided
        class ServiceE:
            @classmethod
            def create(cls, service_a: IServiceA):
                return cls()

        self.mock_service_entry_collection.__contains__.side_effect = lambda x: x == IServiceA
        self.mock_service_entry_collection.get.return_value = Mock(
            constructor=ServiceA, lifetime=ServiceLife.TRANSIENT
        )

        service_instance = self.resolver._create_instance(ServiceE.create, overrides={}, binding=ServiceE)
        self.assertIsInstance(service_instance, ServiceE)