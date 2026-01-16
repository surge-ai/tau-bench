import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_search_by_field_value import SearchByFieldValue


class TestSearchByFieldValue(unittest.TestCase):
    def setUp(self):
        """Set up test data with various entities."""
        self.data: Dict[str, Any] = {
            "order": {
                "order1": {"id": "order1", "customerId": "customer1", "status": "paid"},
                "order2": {"id": "order2", "customerId": "customer2", "status": "pending"},
                "order3": {"id": "order3", "customerId": "customer1", "status": "paid"},
                "order4": {"id": "order4", "customerId": "customer3", "status": "fulfilled"},
            },
            "support_ticket": {
                "ticket1": {"id": "ticket1", "customerId": "customer1", "status": "open", "priority": "high"},
                "ticket2": {"id": "ticket2", "customerId": "customer2", "status": "resolved", "priority": "normal"},
                "ticket3": {"id": "ticket3", "customerId": "customer3", "status": "open", "priority": "high"},
            },
            "product": {
                "prod1": {"id": "prod1", "name": "Gaming Mouse", "category": "mouse", "price": 59.99},
                "prod2": {"id": "prod2", "name": "Keyboard", "category": "keyboard", "price": 129.99},
                "prod3": {"id": "prod3", "name": "Monitor", "category": "monitor", "price": 299.99},
            },
        }

    def test_search_by_status(self):
        """Test searching orders by status."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="order",
            field_name="status",
            field_value="paid",
        )

        self.assertEqual(result["entity_type"], "order")
        self.assertEqual(result["field_name"], "status")
        self.assertEqual(result["field_value"], "paid")
        self.assertEqual(result["count"], 2)
        order_ids = {o["id"] for o in result["results"]}
        self.assertIn("order1", order_ids)
        self.assertIn("order3", order_ids)

    def test_search_by_customer_id(self):
        """Test searching by customerId."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="order",
            field_name="customerId",
            field_value="customer1",
        )

        self.assertEqual(result["count"], 2)
        order_ids = {o["id"] for o in result["results"]}
        self.assertIn("order1", order_ids)
        self.assertIn("order3", order_ids)

    def test_search_tickets_by_priority(self):
        """Test searching tickets by priority."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="ticket",
            field_name="priority",
            field_value="high",
        )

        self.assertEqual(result["count"], 2)
        ticket_ids = {t["id"] for t in result["results"]}
        self.assertIn("ticket1", ticket_ids)
        self.assertIn("ticket3", ticket_ids)

    def test_search_by_category(self):
        """Test searching products by category."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="product",
            field_name="category",
            field_value="mouse",
        )

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["id"], "prod1")

    def test_search_case_insensitive_string(self):
        """Test that string comparison is case-insensitive."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="order",
            field_name="status",
            field_value="PAID",  # Uppercase
        )

        # Should find orders with "paid" status
        self.assertEqual(result["count"], 2)

    def test_search_numeric_field(self):
        """Test searching by numeric field."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="product",
            field_name="price",
            field_value=59.99,
        )

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["id"], "prod1")

    def test_search_no_matches(self):
        """Test search with no matches."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="order",
            field_name="status",
            field_value="nonexistent",
        )

        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["results"]), 0)

    def test_search_invalid_field_returns_error(self):
        """Test searching by field that doesn't exist in schema returns error."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="order",
            field_name="nonexistent_field",
            field_value="value",
        )

        # Should return an error for invalid field name
        self.assertIn("error", result)
        self.assertIn("Invalid field name", result["error"])
        self.assertIn("nonexistent_field", result["error"])
        self.assertIn("valid_fields", result)
        self.assertIn("suggestion", result)

    def test_search_invalid_field_shows_valid_fields(self):
        """Test that error message includes list of valid fields."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="order",
            field_name="invalidField",
            field_value="test",
        )

        self.assertIn("error", result)
        self.assertIn("valid_fields", result)

        # Check that valid fields includes expected order fields
        valid_fields = result["valid_fields"]
        self.assertIn("status", valid_fields)
        self.assertIn("customerId", valid_fields)
        self.assertIn("lineItems", valid_fields)

        # Ensure list is sorted
        self.assertEqual(valid_fields, sorted(valid_fields))

    def test_search_entity_type_alias(self):
        """Test that entity type aliases work."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="ticket",  # Using alias
            field_name="status",
            field_value="open",
        )

        self.assertEqual(result["entity_type"], "ticket")
        self.assertEqual(result["count"], 2)

    def test_search_unknown_entity_type(self):
        """Test with unknown entity type."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="invalid_type",
            field_name="field",
            field_value="value",
        )

        self.assertIn("error", result)
        self.assertIn("Invalid entity_type", result["error"])

    def test_search_empty_entity_table(self):
        """Test with empty entity table."""
        data_with_empty = {"order": {}}

        result = SearchByFieldValue.invoke(
            data_with_empty,
            entity_type="order",
            field_name="status",
            field_value="paid",
        )

        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["results"]), 0)

    def test_search_no_entity_table(self):
        """Test when entity table doesn't exist."""
        data_without_orders = {"support_ticket": {}}

        result = SearchByFieldValue.invoke(
            data_without_orders,
            entity_type="order",
            field_name="status",
            field_value="paid",
        )

        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["results"]), 0)

    def test_search_non_dict_entity_table(self):
        """Test when entity table is not a dict."""
        self.data["order"] = "not_a_dict"

        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="order",
            field_name="status",
            field_value="paid",
        )

        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["results"]), 0)

    def test_search_invalid_entity_format(self):
        """Test when entity is not a dict."""
        self.data["order"]["invalid"] = "not_a_dict"

        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="order",
            field_name="status",
            field_value="paid",
        )

        # Should skip invalid entity
        self.assertEqual(result["count"], 2)

    def test_search_entities_with_null_field(self):
        """Test handling entities with null field value."""
        self.data["order"]["order5"] = {
            "id": "order5",
            "customerId": "customer4",
            "status": None,
        }

        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="order",
            field_name="status",
            field_value="paid",
        )

        # order5 should not match
        order_ids = {o["id"] for o in result["results"]}
        self.assertNotIn("order5", order_ids)

    def test_search_string_field_with_valid_category(self):
        """Test searching by string field with valid category."""
        # All products already have category field, just search for existing one
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="product",
            field_name="category",
            field_value="keyboard",
        )

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["id"], "prod2")

    def test_search_string_vs_numeric_mismatch(self):
        """Test that string and numeric values don't match."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="product",
            field_name="price",
            field_value="59.99",  # String instead of number
        )

        # Should not match because types differ
        self.assertEqual(result["count"], 0)

    def test_search_complete_entities_returned(self):
        """Test that complete entity objects are returned."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="order",
            field_name="status",
            field_value="paid",
        )

        entity = result["results"][0]
        self.assertIn("id", entity)
        self.assertIn("customerId", entity)
        self.assertIn("status", entity)

    def test_search_all_valid_entity_types(self):
        """Test all valid entity types."""
        entity_types = [
            ("customer", "id", "customer1"),
            ("order", "status", "paid"),
            ("ticket", "status", "open"),
            ("support_ticket", "status", "open"),
            ("payment", "status", "pending"),
            ("shipment", "status", "in_transit"),
            ("product", "category", "mouse"),
        ]

        # Add minimal data for missing types
        self.data.setdefault("customer", {})["customer1"] = {"id": "customer1"}
        self.data.setdefault("payment", {})["payment1"] = {"id": "payment1", "status": "pending"}
        self.data.setdefault("shipment", {})["shipment1"] = {"id": "shipment1", "status": "in_transit"}

        for entity_type, field, value in entity_types:
            result = SearchByFieldValue.invoke(
                self.data,
                entity_type=entity_type,
                field_name=field,
                field_value=value,
            )

            # Should not error
            self.assertIn("results", result)
            self.assertIn("count", result)

    def test_search_case_preserves_original_value(self):
        """Test that original values are preserved in results."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="order",
            field_name="status",
            field_value="paid",
        )

        # Check that original case is preserved
        for order in result["results"]:
            self.assertEqual(order["status"], "paid")  # lowercase in data

    def test_search_response_structure(self):
        """Test that response has correct structure."""
        result = SearchByFieldValue.invoke(
            self.data,
            entity_type="order",
            field_name="status",
            field_value="paid",
        )

        self.assertIn("entity_type", result)
        self.assertIn("field_name", result)
        self.assertIn("field_value", result)
        self.assertIn("results", result)
        self.assertIn("count", result)

        self.assertIsInstance(result["results"], list)
        self.assertIsInstance(result["count"], int)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchByFieldValue.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "search_by_field_value")
        self.assertIn("description", info["function"])
        self.assertIn("Case-insensitive", info["function"]["description"])
        self.assertIn("camelCase", info["function"]["description"])
        self.assertIn("parameters", info["function"])
        self.assertIn("entity_type", info["function"]["parameters"]["properties"])
        self.assertIn("field_name", info["function"]["parameters"]["properties"])
        self.assertIn("field_value", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("entity_type", required)
        self.assertIn("field_name", required)
        self.assertIn("field_value", required)


if __name__ == "__main__":
    unittest.main()
