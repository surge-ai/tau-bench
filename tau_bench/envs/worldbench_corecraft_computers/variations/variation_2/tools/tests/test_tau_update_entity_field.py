import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_update_entity_field import UpdateEntityField


class TestUpdateEntityField(unittest.TestCase):
    def setUp(self):
        """Set up test data with various entities."""
        self.data: Dict[str, Any] = {
            "__now": "2025-01-15T12:00:00Z",
            "customer": {
                "customer1": {
                    "id": "customer1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "loyaltyTier": "silver",
                },
            },
            "order": {
                "order1": {
                    "id": "order1",
                    "customerId": "customer1",
                    "status": "pending",
                    "createdAt": "2025-01-10T00:00:00Z",
                    "updatedAt": "2025-01-10T00:00:00Z",
                },
            },
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "status": "new",
                    "priority": "normal",
                    "assignedEmployeeId": None,
                    "createdAt": "2025-01-10T00:00:00Z",
                    "updatedAt": "2025-01-10T00:00:00Z",
                },
            },
            "product": {
                "prod1": {
                    "id": "prod1",
                    "name": "Gaming Mouse",
                    "price": 59.99,
                    "inventory": 100,
                },
            },
        }

    def test_update_string_field(self):
        """Test updating a string field."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            field_name="loyaltyTier",
            field_value="gold",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["entity_type"], "customer")
        self.assertEqual(result["entity_id"], "customer1")
        self.assertEqual(result["field_name"], "loyaltyTier")
        self.assertEqual(result["old_value"], "silver")
        self.assertEqual(result["new_value"], "gold")

        # Verify in data
        self.assertEqual(self.data["customer"]["customer1"]["loyaltyTier"], "gold")

    def test_update_numeric_field(self):
        """Test updating a numeric field."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="product",
            entity_id="prod1",
            field_name="price",
            field_value=69.99,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["old_value"], 59.99)
        self.assertEqual(result["new_value"], 69.99)

        # Verify in data
        self.assertEqual(self.data["product"]["prod1"]["price"], 69.99)

    def test_update_integer_field(self):
        """Test updating an integer field."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="product",
            entity_id="prod1",
            field_name="inventory",
            field_value=150,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["old_value"], 100)
        self.assertEqual(result["new_value"], 150)

    def test_update_status_field(self):
        """Test updating status field."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="order",
            entity_id="order1",
            field_name="status",
            field_value="paid",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["old_value"], "pending")
        self.assertEqual(result["new_value"], "paid")

    def test_update_null_field(self):
        """Test updating a field from None to a value."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="ticket",
            entity_id="ticket1",
            field_name="assignedEmployeeId",
            field_value="emp-001",
        )

        self.assertTrue(result["success"])
        self.assertIsNone(result["old_value"])
        self.assertEqual(result["new_value"], "emp-001")

    def test_update_to_null(self):
        """Test updating a field to None."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            field_name="email",
            field_value=None,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["old_value"], "john@example.com")
        self.assertIsNone(result["new_value"])

    def test_update_nonexistent_field(self):
        """Test updating a field that doesn't exist creates it."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            field_name="newField",
            field_value="newValue",
        )

        self.assertTrue(result["success"])
        self.assertIsNone(result["old_value"])
        self.assertEqual(result["new_value"], "newValue")

        # Verify field was created
        self.assertEqual(self.data["customer"]["customer1"]["newField"], "newValue")

    def test_update_sets_updatedAt_for_orders(self):
        """Test that updatedAt is set for orders."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="order",
            entity_id="order1",
            field_name="status",
            field_value="paid",
        )

        self.assertTrue(result["success"])
        # updatedAt should be updated
        self.assertEqual(self.data["order"]["order1"]["updatedAt"], "2025-01-15T12:00:00Z")

    def test_update_sets_updatedAt_for_tickets(self):
        """Test that updatedAt is set for tickets."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="ticket",
            entity_id="ticket1",
            field_name="priority",
            field_value="high",
        )

        self.assertTrue(result["success"])
        # updatedAt should be updated
        self.assertEqual(self.data["support_ticket"]["ticket1"]["updatedAt"], "2025-01-15T12:00:00Z")

    def test_update_no_updatedAt_for_customers(self):
        """Test that updatedAt is not set for entity types that don't have it."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            field_name="loyaltyTier",
            field_value="gold",
        )

        self.assertTrue(result["success"])
        # Customer doesn't have updatedAt field
        self.assertNotIn("updatedAt", self.data["customer"]["customer1"])

    def test_update_no_updatedAt_for_products(self):
        """Test that updatedAt is not set for products."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="product",
            entity_id="prod1",
            field_name="price",
            field_value=69.99,
        )

        self.assertTrue(result["success"])
        # Product doesn't have updatedAt field
        self.assertNotIn("updatedAt", self.data["product"]["prod1"])

    def test_update_entity_type_alias(self):
        """Test that entity type aliases work."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="ticket",  # Using alias
            entity_id="ticket1",
            field_name="priority",
            field_value="high",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["entity_type"], "ticket")

    def test_update_nonexistent_entity(self):
        """Test updating non-existent entity."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="nonexistent",
            field_name="name",
            field_value="New Name",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_update_unknown_entity_type(self):
        """Test with unknown entity type."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="invalid_type",
            entity_id="entity1",
            field_name="field",
            field_value="value",
        )

        self.assertIn("error", result)
        self.assertIn("Unknown entity type", result["error"])

    def test_update_no_entity_table(self):
        """Test when entity table doesn't exist."""
        data_without_customers = {"order": {}}

        result = UpdateEntityField.invoke(
            data_without_customers,
            entity_type="customer",
            entity_id="customer1",
            field_name="name",
            field_value="New Name",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_update_invalid_entity_table(self):
        """Test when entity table is not a dict."""
        self.data["customer"] = "not_a_dict"

        result = UpdateEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            field_name="name",
            field_value="New Name",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_update_boolean_field(self):
        """Test updating to boolean value."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="product",
            entity_id="prod1",
            field_name="inStock",
            field_value=True,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["new_value"], True)
        self.assertEqual(self.data["product"]["prod1"]["inStock"], True)

    def test_update_object_field(self):
        """Test updating to object/dict value."""
        new_address = {"street": "123 Main St", "city": "New York", "zip": "10001"}

        result = UpdateEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            field_name="address",
            field_value=new_address,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["new_value"], new_address)
        self.assertEqual(self.data["customer"]["customer1"]["address"], new_address)

    def test_update_array_field(self):
        """Test updating to array/list value."""
        new_tags = ["tag1", "tag2", "tag3"]

        result = UpdateEntityField.invoke(
            self.data,
            entity_type="product",
            entity_id="prod1",
            field_name="tags",
            field_value=new_tags,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["new_value"], new_tags)
        self.assertEqual(self.data["product"]["prod1"]["tags"], new_tags)

    def test_update_returns_complete_entity(self):
        """Test that updated entity is returned in response."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            field_name="loyaltyTier",
            field_value="gold",
        )

        updated_entity = result["updated_entity"]
        self.assertEqual(updated_entity["id"], "customer1")
        self.assertEqual(updated_entity["name"], "John Doe")
        self.assertEqual(updated_entity["email"], "john@example.com")
        self.assertEqual(updated_entity["loyaltyTier"], "gold")  # Updated value

    def test_update_mutates_data_in_place(self):
        """Test that data is mutated in place."""
        original_order = self.data["order"]["order1"]

        UpdateEntityField.invoke(
            self.data,
            entity_type="order",
            entity_id="order1",
            field_name="status",
            field_value="paid",
        )

        # Same object reference should be mutated
        self.assertIs(self.data["order"]["order1"], original_order)
        self.assertEqual(original_order["status"], "paid")

    def test_update_uses_custom_timestamp(self):
        """Test that custom timestamp is used for updatedAt."""
        self.data["__now"] = "2025-12-31T23:59:59Z"

        result = UpdateEntityField.invoke(
            self.data,
            entity_type="order",
            entity_id="order1",
            field_name="status",
            field_value="paid",
        )

        self.assertTrue(result["success"])
        self.assertEqual(self.data["order"]["order1"]["updatedAt"], "2025-12-31T23:59:59Z")

    def test_update_all_valid_entity_types(self):
        """Test all valid entity types."""
        entity_types = ["customer", "order", "ticket", "support_ticket", "payment", "product"]

        # Add minimal data for missing types
        self.data.setdefault("payment", {})["payment1"] = {"id": "payment1", "status": "pending"}

        for entity_type in entity_types:
            # Get first entity ID
            if entity_type == "ticket":
                entity_id = "ticket1"
            elif entity_type == "support_ticket":
                entity_id = "ticket1"
            elif entity_type == "payment":
                entity_id = "payment1"
            elif entity_type == "customer":
                entity_id = "customer1"
            elif entity_type == "order":
                entity_id = "order1"
            elif entity_type == "product":
                entity_id = "prod1"
            else:
                continue

            result = UpdateEntityField.invoke(
                self.data,
                entity_type=entity_type,
                entity_id=entity_id,
                field_name="testField",
                field_value="testValue",
            )

            self.assertTrue(result["success"], f"Failed for {entity_type}")

    def test_update_response_structure(self):
        """Test that response has correct structure."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            field_name="loyaltyTier",
            field_value="gold",
        )

        self.assertIn("success", result)
        self.assertIn("entity_type", result)
        self.assertIn("entity_id", result)
        self.assertIn("field_name", result)
        self.assertIn("old_value", result)
        self.assertIn("new_value", result)
        self.assertIn("updated_entity", result)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = UpdateEntityField.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "update_entity_field")
        self.assertIn("description", info["function"])
        # BUG: Documentation says snake_case but actual fields are camelCase
        self.assertIn("snake_case", info["function"]["description"])  # Bug: misleading docs
        self.assertIn("parameters", info["function"])
        self.assertIn("entity_type", info["function"]["parameters"]["properties"])
        self.assertIn("entity_id", info["function"]["parameters"]["properties"])
        self.assertIn("field_name", info["function"]["parameters"]["properties"])
        self.assertIn("field_value", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("entity_type", required)
        self.assertIn("entity_id", required)
        self.assertIn("field_name", required)
        self.assertIn("field_value", required)


if __name__ == "__main__":
    unittest.main()
