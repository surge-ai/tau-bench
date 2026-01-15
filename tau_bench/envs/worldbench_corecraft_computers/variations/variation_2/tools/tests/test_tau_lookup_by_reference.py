import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_lookup_by_reference import LookupByReference


class TestLookupByReference(unittest.TestCase):
    def setUp(self):
        """Set up test data with various entities."""
        self.data: Dict[str, Any] = {
            "customer": {
                "customer1": {
                    "id": "customer1",
                    "name": "John Doe",
                    "email": "john.doe@example.com",
                    "phone": "555-1234",
                },
                "customer2": {
                    "id": "customer2",
                    "name": "Jane Smith",
                    "email": "jane.smith@example.com",
                    "phone": "555-5678",
                },
            },
            "order": {
                "ord-250830-110": {
                    "id": "ord-250830-110",
                    "customerId": "customer1",
                    "status": "paid",
                    "orderNumber": "ORD-12345",
                },
                "ord-250830-111": {
                    "id": "ord-250830-111",
                    "customerId": "customer2",
                    "status": "pending",
                    "orderNumber": "ORD-12346",
                },
            },
            "support_ticket": {
                "tick-250828-001": {
                    "id": "tick-250828-001",
                    "customerId": "customer1",
                    "status": "open",
                    "subject": "Defective product issue",
                },
                "tick-250828-002": {
                    "id": "tick-250828-002",
                    "customerId": "customer2",
                    "status": "resolved",
                    "subject": "Shipping delay question",
                },
            },
            "employee": {
                "emp-001": {
                    "id": "emp-001",
                    "name": "Alice Johnson",
                    "email": "alice@company.com",
                },
                "emp-002": {
                    "id": "emp-002",
                    "name": "Bob Williams",
                    "email": "bob@company.com",
                },
            },
        }

    def test_lookup_by_customer_email(self):
        """Test lookup by customer email."""
        result = LookupByReference.invoke(self.data, reference="john.doe@example.com")

        self.assertEqual(result["query"], "john.doe@example.com")
        self.assertEqual(len(result["results"]["customers"]), 1)
        self.assertEqual(result["results"]["customers"][0]["id"], "customer1")
        self.assertEqual(result["total_count"], 1)

    def test_lookup_by_customer_phone(self):
        """Test lookup by customer phone."""
        result = LookupByReference.invoke(self.data, reference="555-1234")

        self.assertEqual(len(result["results"]["customers"]), 1)
        self.assertEqual(result["results"]["customers"][0]["id"], "customer1")

    def test_lookup_by_customer_name(self):
        """Test lookup by customer name."""
        result = LookupByReference.invoke(self.data, reference="Jane")

        self.assertEqual(len(result["results"]["customers"]), 1)
        self.assertEqual(result["results"]["customers"][0]["name"], "Jane Smith")

    def test_lookup_by_customer_id(self):
        """Test lookup by customer ID."""
        result = LookupByReference.invoke(self.data, reference="customer1")

        self.assertEqual(len(result["results"]["customers"]), 1)
        self.assertEqual(result["results"]["customers"][0]["id"], "customer1")

    def test_lookup_by_order_id(self):
        """Test lookup by order ID."""
        result = LookupByReference.invoke(self.data, reference="ord-250830-110")

        self.assertEqual(len(result["results"]["orders"]), 1)
        self.assertEqual(result["results"]["orders"][0]["id"], "ord-250830-110")

    def test_lookup_by_order_number(self):
        """Test lookup by order number."""
        result = LookupByReference.invoke(self.data, reference="ORD-12345")

        self.assertEqual(len(result["results"]["orders"]), 1)
        self.assertEqual(result["results"]["orders"][0]["id"], "ord-250830-110")

    def test_lookup_by_partial_order_id(self):
        """Test lookup by partial order ID."""
        result = LookupByReference.invoke(self.data, reference="250830")

        # Should find both orders with "250830" in ID
        self.assertEqual(len(result["results"]["orders"]), 2)
        order_ids = {o["id"] for o in result["results"]["orders"]}
        self.assertIn("ord-250830-110", order_ids)
        self.assertIn("ord-250830-111", order_ids)

    def test_lookup_by_ticket_id(self):
        """Test lookup by ticket ID."""
        result = LookupByReference.invoke(self.data, reference="tick-250828-001")

        self.assertEqual(len(result["results"]["tickets"]), 1)
        self.assertEqual(result["results"]["tickets"][0]["id"], "tick-250828-001")

    def test_lookup_by_ticket_subject(self):
        """Test lookup by ticket subject."""
        result = LookupByReference.invoke(self.data, reference="defective")

        self.assertEqual(len(result["results"]["tickets"]), 1)
        self.assertEqual(result["results"]["tickets"][0]["id"], "tick-250828-001")

    def test_lookup_by_employee_email(self):
        """Test lookup by employee email."""
        result = LookupByReference.invoke(self.data, reference="alice@company.com")

        self.assertEqual(len(result["results"]["employees"]), 1)
        self.assertEqual(result["results"]["employees"][0]["id"], "emp-001")

    def test_lookup_by_employee_name(self):
        """Test lookup by employee name."""
        result = LookupByReference.invoke(self.data, reference="Bob")

        self.assertEqual(len(result["results"]["employees"]), 1)
        self.assertEqual(result["results"]["employees"][0]["name"], "Bob Williams")

    def test_lookup_case_insensitive(self):
        """Test that lookup is case-insensitive."""
        result = LookupByReference.invoke(self.data, reference="JOHN.DOE@EXAMPLE.COM")

        self.assertEqual(len(result["results"]["customers"]), 1)
        self.assertEqual(result["results"]["customers"][0]["email"], "john.doe@example.com")

    def test_lookup_partial_match(self):
        """Test partial string matching."""
        result = LookupByReference.invoke(self.data, reference="smith")

        # Should find Jane Smith
        self.assertEqual(len(result["results"]["customers"]), 1)
        self.assertEqual(result["results"]["customers"][0]["name"], "Jane Smith")

    def test_lookup_multiple_results(self):
        """Test lookup returning multiple results across different types."""
        # "john" appears in customer name and email
        result = LookupByReference.invoke(self.data, reference="john")

        self.assertEqual(len(result["results"]["customers"]), 1)
        self.assertGreaterEqual(result["total_count"], 1)

    def test_lookup_no_results(self):
        """Test lookup with no matches."""
        result = LookupByReference.invoke(self.data, reference="nonexistent_reference")

        self.assertEqual(result["total_count"], 0)
        self.assertEqual(len(result["results"]["customers"]), 0)
        self.assertEqual(len(result["results"]["orders"]), 0)
        self.assertEqual(len(result["results"]["tickets"]), 0)
        self.assertEqual(len(result["results"]["employees"]), 0)

    def test_lookup_empty_reference(self):
        """Test lookup with empty string."""
        result = LookupByReference.invoke(self.data, reference="")

        # Empty string matches everything (since it's "in" every string)
        # This is expected behavior based on the implementation
        self.assertGreater(result["total_count"], 0)

    def test_lookup_special_characters(self):
        """Test lookup with special characters."""
        result = LookupByReference.invoke(self.data, reference="555-1234")

        # Should find customer with this phone
        self.assertEqual(len(result["results"]["customers"]), 1)

    def test_lookup_numeric_string(self):
        """Test lookup with numeric string."""
        result = LookupByReference.invoke(self.data, reference="12345")

        # Should find order with orderNumber containing "12345"
        self.assertEqual(len(result["results"]["orders"]), 1)

    def test_lookup_invalid_customer_table(self):
        """Test when customer table is not a dict."""
        self.data["customer"] = "not_a_dict"

        result = LookupByReference.invoke(self.data, reference="john")

        # Should skip invalid table
        self.assertEqual(len(result["results"]["customers"]), 0)

    def test_lookup_invalid_entity_format(self):
        """Test when entity is not a dict."""
        self.data["customer"]["invalid"] = "not_a_dict"

        result = LookupByReference.invoke(self.data, reference="john")

        # Should skip invalid entity but process valid ones
        self.assertEqual(len(result["results"]["customers"]), 1)

    def test_lookup_empty_tables(self):
        """Test with empty entity tables."""
        data_empty = {
            "customer": {},
            "order": {},
            "support_ticket": {},
            "employee": {},
        }

        result = LookupByReference.invoke(data_empty, reference="anything")

        self.assertEqual(result["total_count"], 0)

    def test_lookup_missing_field_values(self):
        """Test handling entities with missing field values."""
        self.data["customer"]["customer3"] = {
            "id": "customer3",
            "name": None,
            "email": None,
            "phone": None,
        }

        result = LookupByReference.invoke(self.data, reference="customer3")

        # Should still find by ID (key)
        customer_ids = {c["id"] for c in result["results"]["customers"]}
        self.assertIn("customer3", customer_ids)

    def test_lookup_searches_entity_key(self):
        """Test that lookup searches the entity key/ID."""
        result = LookupByReference.invoke(self.data, reference="emp-001")

        # Should find by the key itself
        self.assertEqual(len(result["results"]["employees"]), 1)
        self.assertEqual(result["results"]["employees"][0]["id"], "emp-001")

    def test_lookup_complete_entity_returned(self):
        """Test that complete entity objects are returned."""
        result = LookupByReference.invoke(self.data, reference="john.doe@example.com")

        customer = result["results"]["customers"][0]
        self.assertIn("id", customer)
        self.assertIn("name", customer)
        self.assertIn("email", customer)
        self.assertIn("phone", customer)

    def test_lookup_total_count_accuracy(self):
        """Test that total_count matches sum of all results."""
        result = LookupByReference.invoke(self.data, reference="john")

        total = (
            len(result["results"]["customers"]) +
            len(result["results"]["orders"]) +
            len(result["results"]["tickets"]) +
            len(result["results"]["employees"])
        )
        self.assertEqual(result["total_count"], total)

    def test_lookup_response_structure(self):
        """Test that response has correct structure."""
        result = LookupByReference.invoke(self.data, reference="test")

        self.assertIn("results", result)
        self.assertIn("total_count", result)
        self.assertIn("query", result)

        self.assertIn("customers", result["results"])
        self.assertIn("orders", result["results"])
        self.assertIn("tickets", result["results"])
        self.assertIn("employees", result["results"])

        # All should be lists
        self.assertIsInstance(result["results"]["customers"], list)
        self.assertIsInstance(result["results"]["orders"], list)
        self.assertIsInstance(result["results"]["tickets"], list)
        self.assertIsInstance(result["results"]["employees"], list)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = LookupByReference.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "lookup_by_reference")
        self.assertIn("description", info["function"])
        self.assertIn("entity IDs", info["function"]["description"])
        self.assertIn("parameters", info["function"])
        self.assertIn("reference", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("reference", info["function"]["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()
