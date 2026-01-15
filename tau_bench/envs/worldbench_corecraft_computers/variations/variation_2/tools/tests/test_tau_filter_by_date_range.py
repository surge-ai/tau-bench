import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_filter_by_date_range import FilterByDateRange


class TestFilterByDateRange(unittest.TestCase):
    def setUp(self):
        """Set up test data with entities having various date fields."""
        self.data: Dict[str, Any] = {
            "order": {
                "order1": {
                    "id": "order1",
                    "customerId": "customer1",
                    "status": "paid",
                    "createdAt": "2025-01-10T10:00:00Z",
                    "updatedAt": "2025-01-15T10:00:00Z",
                },
                "order2": {
                    "id": "order2",
                    "customerId": "customer2",
                    "status": "pending",
                    "createdAt": "2025-01-20T10:00:00Z",
                    "updatedAt": "2025-01-20T10:00:00Z",
                },
                "order3": {
                    "id": "order3",
                    "customerId": "customer3",
                    "status": "fulfilled",
                    "createdAt": "2025-01-30T10:00:00Z",
                    "updatedAt": "2025-02-01T10:00:00Z",
                },
            },
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "status": "open",
                    "createdAt": "2025-01-05T08:00:00Z",
                    "updatedAt": "2025-01-10T08:00:00Z",
                },
                "ticket2": {
                    "id": "ticket2",
                    "customerId": "customer2",
                    "status": "resolved",
                    "createdAt": "2025-01-15T08:00:00Z",
                    "updatedAt": "2025-01-20T08:00:00Z",
                },
                "ticket3": {
                    "id": "ticket3",
                    "customerId": "customer3",
                    "status": "closed",
                    "createdAt": "2025-02-01T08:00:00Z",
                    "updatedAt": "2025-02-05T08:00:00Z",
                },
            },
            "payment": {
                "payment1": {
                    "id": "payment1",
                    "orderId": "order1",
                    "amount": 100.0,
                    "status": "captured",
                    "createdAt": "2025-01-10T12:00:00Z",
                    "processedAt": "2025-01-11T12:00:00Z",
                },
                "payment2": {
                    "id": "payment2",
                    "orderId": "order2",
                    "amount": 200.0,
                    "status": "pending",
                    "createdAt": "2025-01-25T12:00:00Z",
                    "processedAt": None,
                },
            },
        }

    def test_filter_by_createdAt_with_range(self):
        """Test filtering by createdAt with start and end dates."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
            start_date="2025-01-15T00:00:00Z",
            end_date="2025-01-25T00:00:00Z",
        )

        self.assertEqual(result["entity_type"], "order")
        self.assertEqual(result["date_field"], "createdAt")
        self.assertEqual(result["count"], 1)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["id"], "order2")

    def test_filter_by_start_date_only(self):
        """Test filtering with only start date (inclusive)."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
            start_date="2025-01-20T00:00:00Z",
        )

        self.assertEqual(result["count"], 2)  # order2 and order3
        order_ids = {r["id"] for r in result["results"]}
        self.assertIn("order2", order_ids)
        self.assertIn("order3", order_ids)

    def test_filter_by_end_date_only(self):
        """Test filtering with only end date (inclusive)."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
            end_date="2025-01-20T00:00:00Z",
        )

        # order1 is at 2025-01-10 (before end date) - included
        # order2 is at 2025-01-20T10:00:00Z (after end date of midnight) - excluded
        # order3 is at 2025-01-30 (after end date) - excluded
        self.assertEqual(result["count"], 1)  # Only order1
        order_ids = {r["id"] for r in result["results"]}
        self.assertIn("order1", order_ids)

    def test_filter_no_date_range(self):
        """Test filtering without date range returns all entities."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
        )

        # Without start/end, should return all entities with the field
        self.assertEqual(result["count"], 3)

    def test_filter_tickets_by_updatedAt(self):
        """Test filtering tickets by updatedAt field."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="ticket",
            date_field="updatedAt",
            start_date="2025-01-15T00:00:00Z",
            end_date="2025-01-25T00:00:00Z",
        )

        self.assertEqual(result["entity_type"], "ticket")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["id"], "ticket2")

    def test_filter_payments_by_processedAt(self):
        """Test filtering payments by processedAt field."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="payment",
            date_field="processedAt",
            start_date="2025-01-11T00:00:00Z",
        )

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["id"], "payment1")

    def test_filter_entity_type_alias(self):
        """Test that entity type aliases work."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="ticket",  # Using alias
            date_field="createdAt",
            start_date="2025-01-10T00:00:00Z",
            end_date="2025-01-20T00:00:00Z",
        )

        self.assertEqual(result["entity_type"], "ticket")
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["id"], "ticket2")

    def test_filter_unknown_entity_type(self):
        """Test with unknown entity type."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="invalid_type",
            date_field="createdAt",
        )

        self.assertIn("error", result)
        self.assertIn("Unknown entity type", result["error"])

    def test_filter_invalid_start_date(self):
        """Test with invalid start date format."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
            start_date="invalid-date",
        )

        self.assertIn("error", result)
        self.assertIn("Invalid start_date format", result["error"])

    def test_filter_invalid_end_date(self):
        """Test with invalid end date format."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
            end_date="invalid-date",
        )

        self.assertIn("error", result)
        self.assertIn("Invalid end_date format", result["error"])

    def test_filter_missing_date_field(self):
        """Test filtering by date field that doesn't exist on entities."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="nonexistentDate",
            start_date="2025-01-01T00:00:00Z",
        )

        # Should return empty results
        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["results"]), 0)

    def test_filter_entities_with_null_date_field(self):
        """Test handling entities with null/missing date field."""
        # payment2 has null processedAt
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="payment",
            date_field="processedAt",
            start_date="2025-01-01T00:00:00Z",
        )

        # Should only return payment1 (payment2 has null processedAt)
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["id"], "payment1")

    def test_filter_empty_results(self):
        """Test when no entities match the date range."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
            start_date="2025-12-01T00:00:00Z",
            end_date="2025-12-31T00:00:00Z",
        )

        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["results"]), 0)

    def test_filter_empty_entity_table(self):
        """Test with empty entity table."""
        data_with_empty = {"order": {}}

        result = FilterByDateRange.invoke(
            data_with_empty,
            entity_type="order",
            date_field="createdAt",
        )

        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["results"]), 0)

    def test_filter_no_entity_table(self):
        """Test when entity table doesn't exist."""
        data_without_orders = {"support_ticket": {}}

        result = FilterByDateRange.invoke(
            data_without_orders,
            entity_type="order",
            date_field="createdAt",
        )

        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["results"]), 0)

    def test_filter_non_dict_entity_table(self):
        """Test when entity table is not a dict."""
        self.data["order"] = "not_a_dict"

        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
        )

        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["results"]), 0)

    def test_filter_invalid_entity_format(self):
        """Test handling invalid entity format."""
        self.data["order"]["invalid"] = "not_a_dict"

        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
            start_date="2025-01-01T00:00:00Z",
        )

        # Should skip invalid entity and return valid ones
        self.assertEqual(result["count"], 3)

    def test_filter_entity_with_unparseable_date(self):
        """Test handling entity with unparseable date value."""
        self.data["order"]["order4"] = {
            "id": "order4",
            "createdAt": "invalid-date-format",
        }

        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
            start_date="2025-01-01T00:00:00Z",
        )

        # Should skip order4 and return valid ones
        self.assertEqual(result["count"], 3)
        order_ids = {r["id"] for r in result["results"]}
        self.assertNotIn("order4", order_ids)

    def test_filter_entity_with_non_string_date(self):
        """Test handling entity where date field is not a string."""
        self.data["order"]["order5"] = {
            "id": "order5",
            "createdAt": 12345,  # Not a string
        }

        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
            start_date="2025-01-01T00:00:00Z",
        )

        # Should skip order5
        self.assertEqual(result["count"], 3)
        order_ids = {r["id"] for r in result["results"]}
        self.assertNotIn("order5", order_ids)

    def test_filter_exact_boundary_dates(self):
        """Test filtering with exact boundary dates (inclusive)."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
            start_date="2025-01-10T10:00:00Z",  # Exact match for order1
            end_date="2025-01-20T10:00:00Z",    # Exact match for order2
        )

        # Should include both order1 and order2 (inclusive)
        self.assertEqual(result["count"], 2)
        order_ids = {r["id"] for r in result["results"]}
        self.assertIn("order1", order_ids)
        self.assertIn("order2", order_ids)

    def test_filter_timezone_handling(self):
        """Test that dates with Z suffix are handled correctly."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
            start_date="2025-01-15T00:00:00Z",  # With Z
            end_date="2025-01-25T23:59:59Z",
        )

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["id"], "order2")

    def test_filter_date_without_z_suffix(self):
        """Test dates without Z suffix."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
            start_date="2025-01-15T00:00:00",  # Without Z
            end_date="2025-01-25T23:59:59",
        )

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["id"], "order2")

    def test_filter_returns_complete_entities(self):
        """Test that complete entity objects are returned."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
            start_date="2025-01-10T00:00:00Z",
            end_date="2025-01-10T23:59:59Z",
        )

        self.assertEqual(result["count"], 1)
        entity = result["results"][0]

        # Verify all fields are present
        self.assertEqual(entity["id"], "order1")
        self.assertEqual(entity["customerId"], "customer1")
        self.assertEqual(entity["status"], "paid")
        self.assertIn("createdAt", entity)
        self.assertIn("updatedAt", entity)

    def test_filter_response_structure(self):
        """Test that response has correct structure."""
        result = FilterByDateRange.invoke(
            self.data,
            entity_type="order",
            date_field="createdAt",
            start_date="2025-01-01T00:00:00Z",
            end_date="2025-02-28T23:59:59Z",
        )

        # Verify response structure
        self.assertIn("entity_type", result)
        self.assertIn("date_field", result)
        self.assertIn("start_date", result)
        self.assertIn("end_date", result)
        self.assertIn("results", result)
        self.assertIn("count", result)

        self.assertEqual(result["entity_type"], "order")
        self.assertEqual(result["date_field"], "createdAt")
        self.assertEqual(result["start_date"], "2025-01-01T00:00:00Z")
        self.assertEqual(result["end_date"], "2025-02-28T23:59:59Z")
        self.assertIsInstance(result["results"], list)
        self.assertIsInstance(result["count"], int)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = FilterByDateRange.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "filter_by_date_range")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("entity_type", info["function"]["parameters"]["properties"])
        self.assertIn("date_field", info["function"]["parameters"]["properties"])
        self.assertIn("start_date", info["function"]["parameters"]["properties"])
        self.assertIn("end_date", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("entity_type", required)
        self.assertIn("date_field", required)
        self.assertNotIn("start_date", required)  # Optional
        self.assertNotIn("end_date", required)    # Optional


if __name__ == "__main__":
    unittest.main()
