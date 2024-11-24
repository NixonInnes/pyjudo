import unittest
from unittest.mock import Mock

from pyjudo.core import (
    IServiceEntryCollection,
    IServiceCache,
    IServiceScope,
    IScopeStack,
    ServiceLife,
)
from pyjudo.exceptions import ServiceCircularDependencyError, ServiceResolutionError, ServiceScopeError
from pyjudo.resolver import Resolver


class Test_Resolver(unittest.TestCase):
    def setUp(self):
        self.mock_service_entry_collection: IServiceEntryCollection = Mock(spec=IServiceEntryCollection) # pyright: ignore[reportUninitializedInstanceVariable]
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

