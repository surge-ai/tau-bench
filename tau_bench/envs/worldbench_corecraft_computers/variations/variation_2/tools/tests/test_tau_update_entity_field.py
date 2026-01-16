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

    def test_update_invalid_field_returns_error(self):
        """Test updating a field that doesn't exist in schema returns error."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            field_name="invalidFieldName",
            field_value="newValue",
        )

        # Should return an error for invalid field name
        self.assertIn("error", result)
        self.assertIn("Invalid field name", result["error"])
        self.assertIn("invalidFieldName", result["error"])
        self.assertIn("customer", result["error"])
        self.assertIn("valid_fields", result)
        self.assertIn("suggestion", result)
        self.assertEqual(result["field_name"], "invalidFieldName")
        self.assertEqual(result["entity_type"], "customer")

        # Verify field was NOT created
        self.assertNotIn("invalidFieldName", self.data["customer"]["customer1"])

    def test_update_invalid_field_shows_valid_fields(self):
        """Test that error message includes list of valid fields."""
        result = UpdateEntityField.invoke(
            self.data,
            entity_type="order",
            entity_id="order1",
            field_name="nonExistentField",
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
        self.assertIn("Invalid entity_type", result["error"])
        self.assertIn("invalid_type", result["error"])

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

    def test_update_integer_field_inventory(self):
        """Test updating inventory integer field."""
        # Add initial inventory field
        self.data["product"]["prod1"]["inventory"] = 50

        result = UpdateEntityField.invoke(
            self.data,
            entity_type="product",
            entity_id="prod1",
            field_name="inventory",
            field_value=75,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["old_value"], 50)
        self.assertEqual(result["new_value"], 75)
        self.assertEqual(self.data["product"]["prod1"]["inventory"], 75)

    def test_update_object_field(self):
        """Test updating to object/dict value."""
        new_addresses = [{"street": "123 Main St", "city": "New York", "zip": "10001"}]

        result = UpdateEntityField.invoke(
            self.data,
            entity_type="customer",
            entity_id="customer1",
            field_name="addresses",  # Use valid field from schema
            field_value=new_addresses,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["new_value"], new_addresses)
        self.assertEqual(self.data["customer"]["customer1"]["addresses"], new_addresses)

    def test_update_object_field_specs(self):
        """Test updating specs object field."""
        new_specs = {"weight": "1.5kg", "dimensions": "10x10x5cm"}

        result = UpdateEntityField.invoke(
            self.data,
            entity_type="product",
            entity_id="prod1",
            field_name="specs",  # Use valid field from schema
            field_value=new_specs,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["new_value"], new_specs)
        self.assertEqual(self.data["product"]["prod1"]["specs"], new_specs)

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
        """Test all valid entity types using valid fields."""
        test_cases = [
            ("customer", "customer1", "name", "Updated Name"),
            ("order", "order1", "status", "completed"),
            ("ticket", "ticket1", "status", "resolved"),
            ("support_ticket", "ticket1", "priority", "high"),
            ("payment", "payment1", "status", "completed"),
            ("product", "prod1", "name", "Updated Product"),
        ]

        # Add minimal data for missing types
        self.data.setdefault("payment", {})["payment1"] = {
            "id": "payment1",
            "status": "pending",
            "amount": 100.0,
        }

        for entity_type, entity_id, field_name, field_value in test_cases:
            result = UpdateEntityField.invoke(
                self.data,
                entity_type=entity_type,
                entity_id=entity_id,
                field_name=field_name,
                field_value=field_value,
            )

            self.assertTrue(result.get("success"), f"Failed for {entity_type}: {result.get('error', 'No error message')}")

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
        # Should mention camelCase for field names
        self.assertIn("camelCase", info["function"]["description"])
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
