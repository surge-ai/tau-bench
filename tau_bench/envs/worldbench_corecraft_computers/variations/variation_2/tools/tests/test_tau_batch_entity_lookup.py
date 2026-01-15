import json
import sys
import os
import unittest
from typing import Dict, Any

tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_batch_entity_lookup import BatchEntityLookup


class TestBatchEntityLookup(unittest.TestCase):
    def setUp(self):
        """Set up test data."""
        self.data: Dict[str, Any] = {
            "customer": {
                "cust1": {"id": "cust1", "name": "John"},
                "cust2": {"id": "cust2", "name": "Jane"},
                "cust3": {"id": "cust3", "name": "Bob"},
            },
            "order": {
                "order1": {"id": "order1", "total": 100},
                "order2": {"id": "order2", "total": 200},
            },
            "support_ticket": {
                "ticket1": {"id": "ticket1", "status": "open"},
                "ticket2": {"id": "ticket2", "status": "closed"},
            },
        }

    def test_lookup_multiple_customers(self):
        """Test looking up multiple customers."""
        result = BatchEntityLookup.invoke(
            self.data,
            entity_type="customer",
            entity_ids=["cust1", "cust2"],
        )

        self.assertEqual(result["count"], 2)
        self.assertEqual(len(result["found"]), 2)
        self.assertEqual(len(result["not_found"]), 0)

    def test_lookup_with_not_found(self):
        """Test lookup with some entities not found."""
        result = BatchEntityLookup.invoke(
            self.data,
            entity_type="customer",
            entity_ids=["cust1", "nonexistent", "cust3"],
        )

        self.assertEqual(result["count"], 2)
        self.assertEqual(len(result["found"]), 2)
        self.assertEqual(len(result["not_found"]), 1)
        self.assertIn("nonexistent", result["not_found"])

    def test_lookup_all_not_found(self):
        """Test lookup where no entities are found."""
        result = BatchEntityLookup.invoke(
            self.data,
            entity_type="customer",
            entity_ids=["nonexistent1", "nonexistent2"],
        )

        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["found"]), 0)
        self.assertEqual(len(result["not_found"]), 2)

    def test_lookup_with_ticket_alias(self):
        """Test using 'ticket' alias for 'support_ticket'."""
        result = BatchEntityLookup.invoke(
            self.data,
            entity_type="ticket",
            entity_ids=["ticket1", "ticket2"],
        )

        self.assertEqual(result["entity_type"], "ticket")
        self.assertEqual(result["count"], 2)

    def test_lookup_unknown_entity_type(self):
        """Test lookup with unknown entity type."""
        result = BatchEntityLookup.invoke(
            self.data,
            entity_type="unknown",
            entity_ids=["id1"],
        )

        self.assertIn("error", result)

    def test_lookup_empty_ids_list(self):
        """Test lookup with empty IDs list."""
        result = BatchEntityLookup.invoke(
            self.data,
            entity_type="customer",
            entity_ids=[],
        )

        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["found"]), 0)

    def test_get_info(self):
        """Test get_info returns correct structure."""
        info = BatchEntityLookup.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "batch_entity_lookup")


if __name__ == "__main__":
    unittest.main()
