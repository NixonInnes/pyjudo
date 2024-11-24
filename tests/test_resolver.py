import unittest
from unittest.mock import Mock

from pyjudo.core import (
    IServiceEntryCollection,
    IServiceCache,
    IServiceScope,
    ServiceLife,
)
from pyjudo.resolver import Resolver


class Test_Resolver(unittest.TestCase):
    def setUp(self):
        self.mock_service_entry_collection = Mock(spec=IServiceEntryCollection)
        self.mock_service_cache = Mock(spec=IServiceCache)
        self.mock_service_scope = Mock(spec=IServiceScope)

        self.resolver = Resolver(
            self.mock_service_entry_collection,
            self.mock_service_cache,
            self.mock_service_scope,
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
