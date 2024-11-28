from abc import ABC
import unittest
from unittest.mock import MagicMock, Mock
from typing import Any, Callable

from pyjudo.core import IScopeStack, IServiceCache, IServiceEntryCollection, IServiceScope, IResolver, ServiceLife
from pyjudo.exceptions import ServiceRegistrationError, ServiceResolutionError, ServiceTypeError
from pyjudo.factory import FactoryProxy
from pyjudo.service_container import ServiceContainer


class IMockService(ABC): ...

class MockService(IMockService): ...


class Test_ServiceContainer(unittest.TestCase):
    def setUp(self):
        self.mock_service_entry_collection: IServiceEntryCollection = MagicMock(spec=IServiceEntryCollection)
        self.mock_singleton_cache: IServiceCache = Mock(spec=IServiceCache)
        self.mock_scope_stack: IScopeStack = Mock(spec=IScopeStack)
        self.mock_resolver: IResolver = Mock(spec=IResolver)
        self.mock_scope_factory: Callable[..., IServiceScope] = Mock(return_value=Mock(spec=IServiceScope))

        self.container = ServiceContainer(
            service_entry_collection=self.mock_service_entry_collection,
            singleton_cache=self.mock_singleton_cache,
            scope_stack=self.mock_scope_stack,
            scope_factory=self.mock_scope_factory,
            resolver=self.mock_resolver,
        )

    def test_register_valid_class(self):
        interface = IMockService
        constructor = MockService
        self.container.register(interface, constructor, ServiceLife.SINGLETON)

        # Called twice, the first time during construction when the service container adds itself.
        self.assertEqual(self.mock_service_entry_collection.set.call_count, 2)
        entry = self.mock_service_entry_collection.set.call_args[0][1]
        self.assertEqual(entry.constructor, constructor)
        self.assertEqual(entry.lifetime, ServiceLife.SINGLETON)

    def test_register_invalid_class(self):
        interface = IMockService
        constructor = Mock()

        with self.assertRaises(ServiceRegistrationError):
            self.container.register(interface, constructor, ServiceLife.SINGLETON)

    def test_register_callable_with_annotation(self):
        def constructor() -> MockService:
            return MockService()

        self.container.register(IMockService, constructor, ServiceLife.SINGLETON)

        # Called twice, the first time during construction when the service container adds itself.
        self.assertEqual(self.mock_service_entry_collection.set.call_count, 2)

    def test_register_callable_missing_annotation(self):
        def constructor():
            return MockService()

        with self.assertRaises(ServiceRegistrationError):
            self.container.register(IMockService, constructor, ServiceLife.SINGLETON)

    def test_inject_decorator(self):
        @self.container.inject
        def func(arg1: Any, arg2: Any) -> Any:
            pass

        func(arg1=1, arg2=2)
        self.mock_resolver.resolve_anonymous.assert_called_once()

    def test_unregister(self):
        interface = IMockService
        constructor = MockService
        self.container.unregister(interface)
        self.mock_service_entry_collection.remove.assert_called_once_with(interface)

    def test_add_transient(self):
        interface = IMockService
        constructor = MockService
        self.container.add_transient(interface, constructor)
        # Called twice, the first time during construction when the service container adds itself.
        self.assertEqual(self.mock_service_entry_collection.set.call_count, 2)

    def test_add_scoped(self):
        interface = IMockService
        constructor = MockService
        self.container.add_scoped(interface, constructor)
        # Called twice, the first time during construction when the service container adds itself.
        self.assertEqual(self.mock_service_entry_collection.set.call_count, 2)

    def test_add_singleton(self):
        interface = IMockService
        constructor = MockService
        self.container.add_singleton(interface, constructor)
        # Called twice, the first time during construction when the service container adds itself.
        self.assertEqual(self.mock_service_entry_collection.set.call_count, 2)

    def test_get_valid_service(self):
        interface = IMockService
        service_instance = MockService()
        self.mock_resolver.resolve.return_value = service_instance

        result = self.container.get(interface)
        self.assertIs(result, service_instance)

    def test_get_invalid_service_type(self):
        interface = IMockService
        service_instance = Mock()
        self.mock_resolver.resolve.return_value = service_instance

        with self.assertRaises(ServiceTypeError):
            self.container.get(interface)

    def test_get_factory_registered_service(self):
        interface = IMockService
        self.mock_service_entry_collection.__contains__.return_value = True
        factory = self.container.get_factory(interface)
        self.assertIsInstance(factory, FactoryProxy)

    def test_get_factory_unregistered_service(self):
        interface = IMockService
        self.mock_service_entry_collection.__contains__.return_value = False

        with self.assertRaises(ServiceResolutionError):
            self.container.get_factory(interface)

    def test_is_registered(self):
        interface = IMockService
        self.mock_service_entry_collection.__contains__.return_value = True
        self.assertTrue(self.container.is_registered(interface))

    def test_create_scope(self):
        scope = self.container.create_scope()
        self.mock_scope_factory.assert_called_once_with(self.mock_scope_stack, self.mock_resolver)
        self.assertIsInstance(scope, IServiceScope)

if __name__ == "__main__":
    unittest.main()
