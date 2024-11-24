import threading
from typing import Any
import unittest
from unittest.mock import Mock

from pyjudo.service_cache import ServiceCache


class Test_ServiceCache(unittest.TestCase):
    def setUp(self):
        self.cache: ServiceCache = ServiceCache() # pyright: ignore[reportUninitializedInstanceVariable]

    def test_get_returns_none_when_not_in_cache(self):
        result = self.cache.get(Mock)
        self.assertIsNone(result)

    def test_add_and_get_instance(self):
        mock_interface = Mock()
        mock_instance = Mock()

        self.cache.add(mock_interface, mock_instance)
        result = self.cache.get(mock_interface)

        self.assertIs(result, mock_instance)

    def test_override_existing_instance(self):
        mock_interface = Mock()
        old_instance = Mock()
        new_instance = Mock()

        self.cache.add(mock_interface, old_instance)
        self.cache.add(mock_interface, new_instance)

        result = self.cache.get(mock_interface)
        self.assertIs(result, new_instance)

    def test_initial_cache(self):
        initial_data: dict[type, Any] = {str: "string_instance", int: 42}
        cache = ServiceCache(initial=initial_data)

        self.assertEqual(cache.get(str), "string_instance")
        self.assertEqual(cache.get(int), 42)
        self.assertIsNone(cache.get(float))

    def test_thread_safety(self):
        def worker(cache: ServiceCache, interface: type, instance: Any):
            cache.add(interface, instance)
            result = cache.get(interface)
            self.assertIs(result, instance)

        threads = []
        for i in range(10):
            thread = threading.Thread(target=worker, args=(self.cache, type(f"MockInterface{i}", (), {}), f"Instance{i}"))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify cache consistency
        self.assertEqual(len(self.cache._cache), 10)  # Accessing internal cache for validation

    