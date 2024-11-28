import unittest
from unittest.mock import Mock

from pyjudo.core import IServiceScope, IScopeStack, IResolver, IServiceCache
from pyjudo.disposable import Disposable
from pyjudo.service_scope import ServiceScope


class TestServiceScope(unittest.TestCase):
    def setUp(self):
        self.mock_cache = Mock(spec=IServiceCache)
        self.mock_stack = Mock(spec=IScopeStack)
        self.mock_resolver = Mock(spec=IResolver)
        self.scope = ServiceScope(self.mock_cache, self.mock_stack, self.mock_resolver)

    def test_get_resolves_instance(self):
        interface = Mock()
        instance = Mock()
        self.mock_resolver.resolve.return_value = instance

        result = self.scope.get(interface, key="value")
        self.assertEqual(result, instance)
        self.mock_resolver.resolve.assert_called_once_with(interface, {"key": "value"})

    def test_get_instance_retrieves_from_cache(self):
        interface = Mock()
        instance = Mock()
        self.mock_cache.get.return_value = instance

        result = self.scope.get_instance(interface)
        self.assertEqual(result, instance)
        self.mock_cache.get.assert_called_once_with(interface)

    def test_add_instance_stores_in_cache_and_registers_disposable(self):
        interface = Mock()
        instance = Mock(spec=Disposable)
        self.scope.add_instance(interface, instance)

        self.mock_cache.add.assert_called_once_with(interface, instance)
        self.assertIn(instance, self.scope.disposables)

    def test_add_instance_non_disposable(self):
        interface = Mock()
        instance = Mock()

        self.scope.add_instance(interface, instance)

        self.mock_cache.add.assert_called_once_with(interface, instance)
        self.assertNotIn(instance, self.scope.disposables)

    def test_item_access_uses_get(self):
        interface = Mock()
        self.scope.get = Mock(return_value="mock_instance")
        getter = self.scope[interface]

        result = getter(key="value")
        self.assertEqual(result, "mock_instance")
        self.scope.get.assert_called_once_with(interface, key="value")

    def test_enter_pushes_to_stack(self):
        with self.scope as entered_scope:
            self.assertEqual(entered_scope, self.scope)
            self.mock_stack.push.assert_called_once_with(self.scope)

    def test_exit_pops_stack_and_disposes_disposables(self):
        disposable1 = Mock(spec=Disposable)
        disposable2 = Mock(spec=Disposable)
        self.scope.disposables.extend([disposable1, disposable2])

        with self.scope:
            pass  # Exiting the scope triggers __exit__

        self.mock_stack.pop.assert_called_once()
        disposable1.dispose.assert_called_once()
        disposable2.dispose.assert_called_once()
