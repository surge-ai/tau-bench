import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_get_entity_field import GetEntityField


class TestGetEntityField(unittest.TestCase):
    def setUp(self):
        """Set up test data with various entities."""
        self.data: Dict[str, Any] = {
            "customer": {
                "customer1": {
                    "id": "customer1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "555-1234",
                    "loyaltyTier": "gold",
                },
            },
            "order": {
                "order1": {
                    "id": "order1",
                    "customerId": "customer1",
                    "status": "paid",
                    "createdAt": "2025-01-10T10:00:00Z",
                    "updatedAt": "2025-01-15T10:00:00Z",
                },
            },
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "status": "open",
                    "priority": "high",
                    "subject": "Defective product",
                },
            },
            "product": {
                "prod1": {
                    "id": "prod1",
                    "name": "Gaming Mouse",
                    "price": 59.99,
                    "category": "mouse",
                    "brand": "LogiTech",
                },
            },
        }

    def test_get_single_field(self):
        """Test getting a single field from an entity."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            fields=["name"],
        )

        self.assertEqual(result["entity_id"], "customer1")
        self.assertEqual(result["entity_type"], "customer")
        self.assertIn("fields", result)
        self.assertEqual(result["fields"]["name"], "John Doe")

    def test_get_multiple_fields(self):
        """Test getting multiple fields from an entity."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            fields=["name", "email", "loyaltyTier"],
        )

        self.assertEqual(len(result["fields"]), 3)
        self.assertEqual(result["fields"]["name"], "John Doe")
        self.assertEqual(result["fields"]["email"], "john@example.com")
        self.assertEqual(result["fields"]["loyaltyTier"], "gold")

    def test_get_all_fields(self):
        """Test getting all fields when no fields specified."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
        )

        # Should return entire entity
        self.assertEqual(result["fields"]["id"], "customer1")
        self.assertEqual(result["fields"]["name"], "John Doe")
        self.assertEqual(result["fields"]["email"], "john@example.com")
        self.assertEqual(result["fields"]["phone"], "555-1234")
        self.assertEqual(result["fields"]["loyaltyTier"], "gold")

    def test_get_nonexistent_field(self):
        """Test getting a field that doesn't exist."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            fields=["nonexistent"],
        )

        # Should return None for nonexistent field
        self.assertIn("nonexistent", result["fields"])
        self.assertIsNone(result["fields"]["nonexistent"])

    def test_get_mixed_existent_and_nonexistent_fields(self):
        """Test getting mix of existing and non-existing fields."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            fields=["name", "nonexistent", "email"],
        )

        self.assertEqual(result["fields"]["name"], "John Doe")
        self.assertIsNone(result["fields"]["nonexistent"])
        self.assertEqual(result["fields"]["email"], "john@example.com")

    def test_get_field_from_order(self):
        """Test getting fields from order entity."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="order",
            entity_id="order1",
            fields=["status", "customerId"],
        )

        self.assertEqual(result["entity_type"], "order")
        self.assertEqual(result["fields"]["status"], "paid")
        self.assertEqual(result["fields"]["customerId"], "customer1")

    def test_get_field_from_ticket(self):
        """Test getting fields from ticket entity using alias."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="ticket",  # Using alias
            entity_id="ticket1",
            fields=["status", "priority"],
        )

        self.assertEqual(result["entity_type"], "ticket")
        self.assertEqual(result["fields"]["status"], "open")
        self.assertEqual(result["fields"]["priority"], "high")

    def test_get_field_from_product(self):
        """Test getting fields from product entity."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="product",
            entity_id="prod1",
            fields=["name", "price", "brand"],
        )

        self.assertEqual(result["fields"]["name"], "Gaming Mouse")
        self.assertEqual(result["fields"]["price"], 59.99)
        self.assertEqual(result["fields"]["brand"], "LogiTech")

    def test_get_nonexistent_entity(self):
        """Test with non-existent entity ID."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="nonexistent",
            fields=["name"],
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_get_unknown_entity_type(self):
        """Test with unknown entity type."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="invalid_type",
            entity_id="entity1",
            fields=["field1"],
        )

        self.assertIn("error", result)
        self.assertIn("Unknown entity type", result["error"])

    def test_get_entity_type_alias(self):
        """Test that entity type aliases work."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="ticket",  # Using alias
            entity_id="ticket1",
            fields=["status"],
        )

        self.assertEqual(result["entity_type"], "ticket")
        self.assertEqual(result["fields"]["status"], "open")

    def test_get_empty_fields_list(self):
        """Test with empty fields list."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            fields=[],
        )

        # Empty list should return empty dict of fields
        self.assertEqual(result["fields"], {})

    def test_get_field_no_entity_table(self):
        """Test when entity table doesn't exist."""
        data_without_customers = {"order": {}}

        result = GetEntityField.invoke(
            data_without_customers,
            entity_type="customer",
            entity_id="customer1",
            fields=["name"],
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_get_field_invalid_entity_table(self):
        """Test when entity table is not a dict."""
        self.data["customer"] = "not_a_dict"

        result = GetEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            fields=["name"],
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_get_numeric_field(self):
        """Test getting numeric field."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="product",
            entity_id="prod1",
            fields=["price"],
        )

        self.assertEqual(result["fields"]["price"], 59.99)
        self.assertIsInstance(result["fields"]["price"], float)

    def test_get_nested_field(self):
        """Test getting nested object/array fields."""
        self.data["order"]["order2"] = {
            "id": "order2",
            "customerId": "customer1",
            "lineItems": [
                {"productId": "prod1", "quantity": 2},
                {"productId": "prod2", "quantity": 1},
            ],
        }

        result = GetEntityField.invoke(
            self.data,
            entity_type="order",
            entity_id="order2",
            fields=["lineItems"],
        )

        self.assertIsInstance(result["fields"]["lineItems"], list)
        self.assertEqual(len(result["fields"]["lineItems"]), 2)

    def test_get_field_case_sensitive(self):
        """Test that field names are case-sensitive."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            fields=["loyaltyTier", "loyaltytier"],  # Different cases
        )

        # loyaltyTier should exist, loyaltytier should not
        self.assertEqual(result["fields"]["loyaltyTier"], "gold")
        self.assertIsNone(result["fields"]["loyaltytier"])

    def test_get_all_entity_types(self):
        """Test that all entity types in the map work."""
        entity_types = [
            ("customer", "customer1"),
            ("order", "order1"),
            ("ticket", "ticket1"),
            ("support_ticket", "ticket1"),
            ("product", "prod1"),
        ]

        for entity_type, entity_id in entity_types:
            result = GetEntityField.invoke(
                self.data,
                entity_type=entity_type,
                entity_id=entity_id,
                fields=["id"],
            )

            self.assertIn("fields", result)
            self.assertIn("id", result["fields"])

    def test_response_structure(self):
        """Test that response has correct structure."""
        result = GetEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            fields=["name"],
        )

        self.assertIn("entity_id", result)
        self.assertIn("entity_type", result)
        self.assertIn("fields", result)
        self.assertIsInstance(result["fields"], dict)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = GetEntityField.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "get_entity_field")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("entity_type", info["function"]["parameters"]["properties"])
        self.assertIn("entity_id", info["function"]["parameters"]["properties"])
        self.assertIn("fields", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("entity_type", required)
        self.assertIn("entity_id", required)
        self.assertNotIn("fields", required)  # Optional


if __name__ == "__main__":
    unittest.main()
