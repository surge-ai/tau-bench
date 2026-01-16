import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_query_by_criteria import QueryByCriteria


class TestQueryByCriteria(unittest.TestCase):
    def setUp(self):
        """Set up test data with various entities."""
        self.data: Dict[str, Any] = {
            "product": {
                "prod1": {"id": "prod1", "name": "Gaming Mouse", "price": 59.99, "category": "mouse"},
                "prod2": {"id": "prod2", "name": "Mechanical Keyboard", "price": 129.99, "category": "keyboard"},
                "prod3": {"id": "prod3", "name": "Gaming Headset", "price": 89.99, "category": "headset"},
                "prod4": {"id": "prod4", "name": "USB Cable", "price": 9.99, "category": "cable"},
                "prod5": {"id": "prod5", "name": "27-inch Monitor", "price": 299.99, "category": "monitor"},
            },
            "order": {
                "order1": {"id": "order1", "customerId": "customer1", "status": "paid", "total": 150.0},
                "order2": {"id": "order2", "customerId": "customer2", "status": "pending", "total": 200.0},
                "order3": {"id": "order3", "customerId": "customer1", "status": "paid", "total": 300.0},
                "order4": {"id": "order4", "customerId": "customer3", "status": "fulfilled", "total": 100.0},
            },
            "support_ticket": {
                "ticket1": {"id": "ticket1", "customerId": "customer1", "status": "open", "priority": "high"},
                "ticket2": {"id": "ticket2", "customerId": "customer2", "status": "resolved", "priority": "normal"},
                "ticket3": {"id": "ticket3", "customerId": "customer3", "status": "open", "priority": "high"},
            },
        }

    def test_query_exact_match(self):
        """Test exact match query."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"category": "mouse"},
        )

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["id"], "prod1")

    def test_query_multiple_filters(self):
        """Test query with multiple filters."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="order",
            filters={"customerId": "customer1", "status": "paid"},
        )

        self.assertEqual(result["count"], 2)
        order_ids = {o["id"] for o in result["results"]}
        self.assertIn("order1", order_ids)
        self.assertIn("order3", order_ids)

    def test_query_gte_operator(self):
        """Test greater than or equal to operator."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"price": {"$gte": 100}},
        )

        self.assertEqual(result["count"], 2)
        product_ids = {p["id"] for p in result["results"]}
        self.assertIn("prod2", product_ids)  # 129.99
        self.assertIn("prod5", product_ids)  # 299.99

    def test_query_lte_operator(self):
        """Test less than or equal to operator."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"price": {"$lte": 60}},
        )

        self.assertEqual(result["count"], 2)
        product_ids = {p["id"] for p in result["results"]}
        self.assertIn("prod1", product_ids)  # 59.99
        self.assertIn("prod4", product_ids)  # 9.99

    def test_query_gt_operator(self):
        """Test greater than operator."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"price": {"$gt": 100}},
        )

        self.assertEqual(result["count"], 2)
        product_ids = {p["id"] for p in result["results"]}
        self.assertIn("prod2", product_ids)  # 129.99
        self.assertIn("prod5", product_ids)  # 299.99

    def test_query_lt_operator(self):
        """Test less than operator."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"price": {"$lt": 60}},
        )

        self.assertEqual(result["count"], 2)
        product_ids = {p["id"] for p in result["results"]}
        self.assertIn("prod1", product_ids)  # 59.99
        self.assertIn("prod4", product_ids)  # 9.99

    def test_query_range(self):
        """Test range query with both gte and lte."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"price": {"$gte": 50, "$lte": 150}},
        )

        self.assertEqual(result["count"], 3)
        product_ids = {p["id"] for p in result["results"]}
        self.assertIn("prod1", product_ids)  # 59.99
        self.assertIn("prod2", product_ids)  # 129.99
        self.assertIn("prod3", product_ids)  # 89.99

    def test_query_ne_operator(self):
        """Test not equal operator."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="order",
            filters={"status": {"$ne": "paid"}},
        )

        self.assertEqual(result["count"], 2)
        order_ids = {o["id"] for o in result["results"]}
        self.assertIn("order2", order_ids)  # pending
        self.assertIn("order4", order_ids)  # fulfilled

    def test_query_in_operator(self):
        """Test in operator."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"category": {"$in": ["mouse", "keyboard"]}},
        )

        self.assertEqual(result["count"], 2)
        product_ids = {p["id"] for p in result["results"]}
        self.assertIn("prod1", product_ids)
        self.assertIn("prod2", product_ids)

    def test_query_contains_operator(self):
        """Test contains operator for text search."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"name": {"$contains": "Gaming"}},
        )

        self.assertEqual(result["count"], 2)
        product_ids = {p["id"] for p in result["results"]}
        self.assertIn("prod1", product_ids)  # Gaming Mouse
        self.assertIn("prod3", product_ids)  # Gaming Headset

    def test_query_contains_case_insensitive(self):
        """Test that contains is case-insensitive."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"name": {"$contains": "gaming"}},  # lowercase
        )

        self.assertEqual(result["count"], 2)

    def test_query_list_as_in_operator(self):
        """Test that list value is treated as 'in' operator."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="order",
            filters={"status": ["paid", "fulfilled"]},
        )

        self.assertEqual(result["count"], 3)
        order_ids = {o["id"] for o in result["results"]}
        self.assertIn("order1", order_ids)
        self.assertIn("order3", order_ids)
        self.assertIn("order4", order_ids)

    def test_query_with_limit(self):
        """Test query with limit."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={},
            limit=2,
        )

        self.assertEqual(result["count"], 2)
        self.assertEqual(len(result["results"]), 2)

    def test_query_no_filters(self):
        """Test query with no filters returns all."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
        )

        self.assertEqual(result["count"], 5)

    def test_query_empty_filters(self):
        """Test query with empty filters dict."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={},
        )

        self.assertEqual(result["count"], 5)

    def test_query_no_matches(self):
        """Test query that matches nothing."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"category": "nonexistent"},
        )

        self.assertEqual(result["count"], 0)
        self.assertEqual(len(result["results"]), 0)

    def test_query_unknown_entity_type(self):
        """Test with unknown entity type."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="invalid_type",
            filters={},
        )

        self.assertIn("error", result)
        self.assertIn("Unknown entity type", result["error"])

    def test_query_entity_type_alias(self):
        """Test that entity type aliases work."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="ticket",  # Using alias
            filters={"status": "open"},
        )

        self.assertEqual(result["count"], 2)

    def test_query_invalid_entity_table(self):
        """Test when entity table is not a dict."""
        self.data["product"] = "not_a_dict"

        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={},
        )

        self.assertEqual(result["results"], [])

    def test_query_invalid_entity_format(self):
        """Test when entity is not a dict."""
        self.data["product"]["invalid"] = "not_a_dict"

        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={},
        )

        # Should skip invalid entity
        self.assertEqual(result["count"], 5)

    def test_query_missing_field(self):
        """Test query on field that doesn't exist."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"nonexistent_field": "value"},
        )

        # No matches since field doesn't exist
        self.assertEqual(result["count"], 0)

    def test_query_null_field_value(self):
        """Test handling entities with null field values."""
        self.data["order"]["order5"] = {
            "id": "order5",
            "customerId": "customer4",
            "status": None,
        }

        result = QueryByCriteria.invoke(
            self.data,
            entity_type="order",
            filters={"status": "paid"},
        )

        # order5 should not match
        order_ids = {o["id"] for o in result["results"]}
        self.assertNotIn("order5", order_ids)

    def test_query_combined_operators(self):
        """Test combining multiple operators on same field."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"price": {"$gte": 50, "$lte": 100}},
        )

        self.assertEqual(result["count"], 3)

    def test_query_multiple_fields_with_operators(self):
        """Test combining operators across multiple fields."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="order",
            filters={
                "status": "paid",
                "total": {"$gte": 200},
            },
        )

        self.assertEqual(result["count"], 1)
        self.assertEqual(result["results"][0]["id"], "order3")

    def test_query_limit_less_than_matches(self):
        """Test limit smaller than number of matches."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={},
            limit=3,
        )

        self.assertEqual(len(result["results"]), 3)
        self.assertEqual(result["count"], 3)

    def test_query_limit_greater_than_matches(self):
        """Test limit larger than number of matches."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"category": "mouse"},
            limit=10,
        )

        self.assertEqual(result["count"], 1)

    def test_query_complete_entities_returned(self):
        """Test that complete entity objects are returned."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"category": "mouse"},
        )

        entity = result["results"][0]
        self.assertIn("id", entity)
        self.assertIn("name", entity)
        self.assertIn("price", entity)
        self.assertIn("category", entity)

    def test_query_response_structure(self):
        """Test that response has correct structure."""
        result = QueryByCriteria.invoke(
            self.data,
            entity_type="product",
            filters={"category": "mouse"},
        )

        self.assertIn("results", result)
        self.assertIn("count", result)
        self.assertIsInstance(result["results"], list)
        self.assertIsInstance(result["count"], int)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = QueryByCriteria.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "query_by_criteria")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("entity_type", info["function"]["parameters"]["properties"])
        self.assertIn("filters", info["function"]["parameters"]["properties"])
        self.assertIn("limit", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("entity_type", info["function"]["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()
