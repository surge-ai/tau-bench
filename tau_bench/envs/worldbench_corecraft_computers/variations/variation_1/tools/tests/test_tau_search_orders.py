import json
import unittest
from typing import Dict, Any

from ..tau_search_orders import SearchOrders


class TestSearchOrders(unittest.TestCase):
    def setUp(self):
        """Set up test data with orders."""
        self.data: Dict[str, Any] = {
            "order": {
                "order1": {
                    "id": "order1",
                    "customerId": "customer1",
                    "status": "paid",
                    "lineItems": [
                        {"productId": "prod1", "qty": 1, "price": 100.0}
                    ],
                },
                "order2": {
                    "id": "order2",
                    "customerId": "customer1",
                    "status": "pending",
                    "lineItems": [
                        {"productId": "prod2", "qty": 2, "price": 50.0}
                    ],
                },
                "order3": {
                    "id": "order3",
                    "customerId": "customer2",
                    "status": "paid",
                    "lineItems": [
                        {"productId": "prod3", "qty": 1, "price": 200.0}
                    ],
                },
            }
        }

    def test_search_orders_no_filters(self):
        """Test searching orders with no filters."""
        result = SearchOrders.invoke(self.data)
        result_list = result

        # Should return all orders
        self.assertIsInstance(result_list, list)
        self.assertEqual(len(result_list), 3)

        # Check structure of first order
        if result_list:
            order = result_list[0]
            self.assertIn("id", order)
            self.assertIn("customerId", order)
            self.assertIn("status", order)

    def test_search_orders_by_id(self):
        """Test searching orders by exact ID."""
        result = SearchOrders.invoke(
            self.data,
            order_id="order1",
        )
        result_list = result

        # Should return exactly one order
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["id"], "order1")
        self.assertEqual(result_list[0]["customerId"], "customer1")

    def test_search_orders_by_customer_id(self):
        """Test searching orders by customer ID."""
        result = SearchOrders.invoke(
            self.data,
            customer_id="customer1",
        )
        result_list = result

        # Should return orders for customer1
        self.assertEqual(len(result_list), 2)
        for order in result_list:
            self.assertEqual(order["customerId"], "customer1")

    def test_search_orders_by_status(self):
        """Test searching orders by status."""
        result = SearchOrders.invoke(
            self.data,
            status="paid",
        )
        result_list = result

        # Should return orders with paid status
        self.assertEqual(len(result_list), 2)
        for order in result_list:
            self.assertEqual(order["status"], "paid")

    def test_search_orders_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchOrders.invoke(
            self.data,
            customer_id="customer1",
            status="paid",
        )
        result_list = result

        # Should match orders that satisfy all filters
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["id"], "order1")
        self.assertEqual(result_list[0]["customerId"], "customer1")
        self.assertEqual(result_list[0]["status"], "paid")

    def test_search_orders_no_results(self):
        """Test search with filters that match no orders."""
        result = SearchOrders.invoke(
            self.data,
            order_id="nonexistent",
        )
        result_list = result

        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_search_orders_all_filters(self):
        """Test searching with all three filters."""
        result = SearchOrders.invoke(
            self.data,
            order_id="order1",
            customer_id="customer1",
            status="paid",
        )
        result_list = result

        # Should return order1
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["id"], "order1")

    def test_search_orders_invalid_status(self):
        """Test that invalid status raises ValueError."""
        result = SearchOrders.invoke(
            self.data,
            status="pai",  # Invalid status
        )
        self.assertIn("error", result)
        self.assertIn("Invalid status", result["error"])

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchOrders.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "searchOrders")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("order_id", info["function"]["parameters"]["properties"])
        self.assertIn("customer_id", info["function"]["parameters"]["properties"])
        self.assertIn("status", info["function"]["parameters"]["properties"])


if __name__ == "__main__":
    unittest.main()
