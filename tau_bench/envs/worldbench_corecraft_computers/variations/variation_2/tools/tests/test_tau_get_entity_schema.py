import json
import sys
import os
import unittest
from typing import Dict, Any

tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_get_entity_schema import GetEntitySchema


class TestGetEntitySchema(unittest.TestCase):
    def setUp(self):
        """Set up test data with various entities."""
        self.data: Dict[str, Any] = {
            "order": {
                "order1": {
                    "id": "order1",
                    "type": "order",
                    "customerId": "customer1",
                    "status": "paid",
                    "lineItems": json.dumps([{"productId": "prod1", "qty": 1, "price": 100.0}]),
                    "createdAt": "2025-01-10T10:00:00Z",
                    "updatedAt": "2025-01-10T10:00:00Z",
                },
                "order2": {
                    "id": "order2",
                    "type": "order",
                    "customerId": "customer2",
                    "status": "pending",
                    "lineItems": json.dumps([]),
                    "buildId": "build1",
                    "createdAt": "2025-01-11T10:00:00Z",
                    "updatedAt": "2025-01-11T10:00:00Z",
                },
            },
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "type": "support_ticket",
                    "customerId": "customer1",
                    "orderId": "order1",
                    "status": "open",
                    "priority": "high",
                    "subject": "Help needed",
                    "ticketType": "order_issue",
                    "createdAt": "2025-01-10T10:00:00Z",
                    "updatedAt": "2025-01-10T10:00:00Z",
                },
            },
            "customer": {
                "customer1": {
                    "id": "customer1",
                    "type": "customer",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "loyaltyTier": "gold",
                },
            },
        }

    def test_get_schema_basic(self):
        """Test getting schema for orders."""
        result_str = GetEntitySchema.invoke(
            self.data,
            entity_type="order",
        )
        result = json.loads(result_str)

        self.assertEqual(result["entity_type"], "order")
        self.assertEqual(result["data_key"], "order")
        self.assertEqual(result["total_entities"], 2)
        self.assertIn("fields", result)
        self.assertIn("field_types", result)

    def test_get_schema_all_fields(self):
        """Test that all fields are discovered."""
        result = json.loads(GetEntitySchema.invoke(
            self.data,
            entity_type="order",
        ))

        all_fields = result["fields"]["all"]
        # Should include fields from both orders
        self.assertIn("id", all_fields)
        self.assertIn("type", all_fields)
        self.assertIn("customerId", all_fields)
        self.assertIn("status", all_fields)
        self.assertIn("lineItems", all_fields)
        self.assertIn("buildId", all_fields)
        self.assertIn("createdAt", all_fields)
        self.assertIn("updatedAt", all_fields)

    def test_get_schema_categorizes_fields(self):
        """Test that fields are properly categorized."""
        result = json.loads(GetEntitySchema.invoke(
            self.data,
            entity_type="order",
        ))

        fields = result["fields"]

        # System fields
        self.assertIn("id", fields["system"])
        self.assertIn("type", fields["system"])

        # Timestamp fields
        self.assertIn("createdAt", fields["timestamps"])
        self.assertIn("updatedAt", fields["timestamps"])

        # Reference fields
        self.assertIn("customerId", fields["references"])
        self.assertIn("buildId", fields["references"])

        # Data fields
        self.assertIn("status", fields["data"])
        self.assertIn("lineItems", fields["data"])

    def test_get_schema_field_types(self):
        """Test that field types are inferred correctly."""
        result = json.loads(GetEntitySchema.invoke(
            self.data,
            entity_type="order",
        ))

        field_types = result["field_types"]

        self.assertEqual(field_types["id"], "string")
        self.assertEqual(field_types["status"], "string")
        self.assertEqual(field_types["lineItems"], "string")

    def test_get_schema_ticket_alias(self):
        """Test using 'ticket' alias for 'support_ticket'."""
        result = json.loads(GetEntitySchema.invoke(
            self.data,
            entity_type="ticket",
        ))

        self.assertEqual(result["entity_type"], "ticket")
        self.assertEqual(result["data_key"], "support_ticket")
        self.assertEqual(result["total_entities"], 1)

    def test_get_schema_support_ticket_fields(self):
        """Test getting schema for support tickets."""
        result = json.loads(GetEntitySchema.invoke(
            self.data,
            entity_type="support_ticket",
        ))

        all_fields = result["fields"]["all"]
        self.assertIn("priority", all_fields)
        self.assertIn("subject", all_fields)
        self.assertIn("ticketType", all_fields)
        self.assertIn("orderId", all_fields)

    def test_get_schema_customer_fields(self):
        """Test getting schema for customers."""
        result = json.loads(GetEntitySchema.invoke(
            self.data,
            entity_type="customer",
        ))

        all_fields = result["fields"]["all"]
        self.assertIn("name", all_fields)
        self.assertIn("email", all_fields)
        self.assertIn("loyaltyTier", all_fields)

    def test_get_schema_unknown_entity_type(self):
        """Test that unknown entity type returns error."""
        result = json.loads(GetEntitySchema.invoke(
            self.data,
            entity_type="unknown_type",
        ))

        self.assertIn("error", result)

    def test_get_schema_empty_entity_table(self):
        """Test schema with no entities."""
        empty_data = {"product": {}}

        result = json.loads(GetEntitySchema.invoke(
            empty_data,
            entity_type="product",
        ))

        self.assertEqual(result["entity_type"], "product")
        self.assertEqual(result["fields"]["all"], [])
        self.assertEqual(result["total_entities"], 0)

    def test_get_schema_no_entity_table(self):
        """Test schema when entity table doesn't exist."""
        empty_data = {}

        result = json.loads(GetEntitySchema.invoke(
            empty_data,
            entity_type="payment",
        ))

        self.assertEqual(result["entity_type"], "payment")
        # When table doesn't exist, get_entity_table returns None and we get full structure
        self.assertEqual(result["total_entities"], 0)
        self.assertEqual(result["fields"]["all"], [])

    def test_get_schema_field_count(self):
        """Test that field count is accurate."""
        result = json.loads(GetEntitySchema.invoke(
            self.data,
            entity_type="order",
        ))

        field_count = result["field_count"]
        all_fields = result["fields"]["all"]

        self.assertEqual(field_count, len(all_fields))
        self.assertGreater(field_count, 0)

    def test_get_schema_sorted_fields(self):
        """Test that fields are returned sorted."""
        result = json.loads(GetEntitySchema.invoke(
            self.data,
            entity_type="order",
        ))

        all_fields = result["fields"]["all"]
        self.assertEqual(all_fields, sorted(all_fields))

    def test_get_schema_with_various_types(self):
        """Test field type detection with various data types."""
        data_with_types = {
            "product": {
                "prod1": {
                    "id": "prod1",
                    "name": "Widget",
                    "price": 99.99,
                    "inventory": 50,
                    "available": True,
                    "tags": ["electronics", "gadget"],
                    "specs": {"weight": 1.5, "color": "blue"},
                    "discontinued": None,
                }
            }
        }

        result = json.loads(GetEntitySchema.invoke(
            data_with_types,
            entity_type="product",
        ))

        field_types = result["field_types"]
        self.assertEqual(field_types["name"], "string")
        self.assertEqual(field_types["price"], "number")
        self.assertEqual(field_types["inventory"], "integer")
        self.assertEqual(field_types["available"], "boolean")
        self.assertEqual(field_types["tags"], "array")
        self.assertEqual(field_types["specs"], "object")
        self.assertEqual(field_types["discontinued"], "null")

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = GetEntitySchema.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "get_entity_schema")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("entity_type", info["function"]["parameters"]["properties"])


if __name__ == "__main__":
    unittest.main()
