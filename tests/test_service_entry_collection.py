import unittest
from unittest.mock import Mock
import threading

from pyjudo.core import ServiceEntry
from pyjudo.exceptions import ServiceRegistrationError, ServiceResolutionError
from pyjudo.service_entry_collection import ServiceEntryCollection


class Test_ServiceEntryCollection(unittest.TestCase):
    def setUp(self):
        self.collection = ServiceEntryCollection()

    def test_set_and_get_service(self):
        interface = Mock()
        entry = ServiceEntry(constructor=Mock(), lifetime=Mock())

        self.collection.set(interface, entry)
        retrieved_entry = self.collection.get(interface)

        self.assertIs(retrieved_entry, entry)

    def test_get_unregistered_service_raises_error(self):
        interface = Mock()

        with self.assertRaises(ServiceResolutionError) as cm:
            self.collection.get(interface)

        self.assertEqual(
            str(cm.exception),
            f"No service registered for: {interface}",
        )

    def test_set_duplicate_service_raises_error(self):
        interface = Mock()
        entry = ServiceEntry(constructor=Mock(), lifetime=Mock())

        self.collection.set(interface, entry)

        with self.assertRaises(ServiceRegistrationError) as cm:
            self.collection.set(interface, entry)

        self.assertEqual(
            str(cm.exception),
            f"Service '{interface}' is already registered.",
        )

    def test_remove_service(self):
        interface = Mock()
        entry = ServiceEntry(constructor=Mock(), lifetime=Mock())

        self.collection.set(interface, entry)
        self.collection.remove(interface)

        with self.assertRaises(ServiceResolutionError):
            self.collection.get(interface)

    def test_contains_service(self):
        interface = Mock()
        entry = ServiceEntry(constructor=Mock(), lifetime=Mock())

        self.collection.set(interface, entry)
        self.assertIn(interface, self.collection)

        self.collection.remove(interface)
        self.assertNotIn(interface, self.collection)

    def test_thread_safety(self):
        def worker(collection, interface, entry):
            collection.set(interface, entry)
            self.assertIn(interface, collection)
            retrieved_entry = collection.get(interface)
            self.assertIs(retrieved_entry, entry)

        threads = []
        for i in range(10):
            interface = type(f"MockInterface{i}", (), {})
            entry = ServiceEntry(constructor=Mock(), lifetime=Mock())
            thread = threading.Thread(target=worker, args=(self.collection, interface, entry))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.assertEqual(len(self.collection._entries), 10)  # Validate internal state
