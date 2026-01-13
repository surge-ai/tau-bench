import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
# We're in tests/ subdirectory, so go up one level to tools/
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

# Import dependencies first
from tau_bench.envs.tool import Tool

# Now import the tool module normally
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from tau_update_order_status import UpdateOrderStatus


class TestUpdateOrderStatus(unittest.TestCase):
    def setUp(self):
        """Set up test data with orders."""
        self.data: Dict[str, Any] = {
            "orders": [
                {
                    "id": "order1",
                    "customerId": "customer1",
                    "status": "pending",
                    "lineItems": [
                        {"productId": "prod1", "qty": 1, "price": 100.0}
                    ],
                },
                {
                    "id": "order2",
                    "customerId": "customer1",
                    "status": "paid",
                    "lineItems": [
                        {"productId": "prod2", "qty": 2, "price": 50.0}
                    ],
                },
                {
                    "id": "order3",
                    "customerId": "customer2",
                    "status": "pending",
                    "lineItems": [
                        {"productId": "prod3", "qty": 1, "price": 200.0}
                    ],
                },
            ]
        }

    def test_update_order_status_basic(self):
        """Test updating order status."""
        result = UpdateOrderStatus.invoke(
            self.data,
            order_id="order1",
            status="paid",
        )
        result_dict = json.loads(result)
        
        # Should return updated=True
        self.assertTrue(result_dict["updated"])
        
        # Should mutate data in place
        order1 = next((o for o in self.data["orders"] if o["id"] == "order1"), None)
        self.assertIsNotNone(order1)
        self.assertEqual(order1["status"], "paid")

    def test_update_order_status_different_statuses(self):
        """Test updating to different status values."""
        statuses = ["paid", "shipped", "delivered", "cancelled", "refunded"]
        
        for status in statuses:
            # Reset order1 status
            order1 = next((o for o in self.data["orders"] if o["id"] == "order1"), None)
            if order1:
                order1["status"] = "pending"
            
            result = UpdateOrderStatus.invoke(
                self.data,
                order_id="order1",
                status=status,
            )
            result_dict = json.loads(result)
            
            self.assertTrue(result_dict["updated"])
            self.assertEqual(order1["status"], status)

    def test_update_order_status_nonexistent_order(self):
        """Test updating non-existent order."""
        result = UpdateOrderStatus.invoke(
            self.data,
            order_id="nonexistent",
            status="paid",
        )
        result_dict = json.loads(result)
        
        # Should return updated=False
        self.assertFalse(result_dict["updated"])
        
        # Data should not be changed
        self.assertEqual(len(self.data["orders"]), 3)

    def test_update_order_status_multiple_updates(self):
        """Test updating the same order multiple times."""
        # First update
        result1 = UpdateOrderStatus.invoke(
            self.data,
            order_id="order1",
            status="paid",
        )
        result_dict1 = json.loads(result1)
        
        self.assertTrue(result_dict1["updated"])
        order1 = next((o for o in self.data["orders"] if o["id"] == "order1"), None)
        self.assertEqual(order1["status"], "paid")
        
        # Second update
        result2 = UpdateOrderStatus.invoke(
            self.data,
            order_id="order1",
            status="shipped",
        )
        result_dict2 = json.loads(result2)
        
        self.assertTrue(result_dict2["updated"])
        self.assertEqual(order1["status"], "shipped")

    def test_update_order_status_other_orders_unchanged(self):
        """Test that other orders are not affected."""
        initial_status_order2 = next(
            (o["status"] for o in self.data["orders"] if o["id"] == "order2"),
            None
        )
        
        result = UpdateOrderStatus.invoke(
            self.data,
            order_id="order1",
            status="paid",
        )
        result_dict = json.loads(result)
        
        self.assertTrue(result_dict["updated"])
        
        # order2 should be unchanged
        order2 = next((o for o in self.data["orders"] if o["id"] == "order2"), None)
        self.assertIsNotNone(order2)
        self.assertEqual(order2["status"], initial_status_order2)
        
        # order3 should be unchanged
        order3 = next((o for o in self.data["orders"] if o["id"] == "order3"), None)
        self.assertIsNotNone(order3)
        self.assertEqual(order3["status"], "pending")

    def test_update_order_status_mutates_data_in_place(self):
        """Test that the tool mutates data in place (write tool behavior)."""
        # Get initial reference to order
        order1_initial = next((o for o in self.data["orders"] if o["id"] == "order1"), None)
        self.assertIsNotNone(order1_initial)
        
        result = UpdateOrderStatus.invoke(
            self.data,
            order_id="order1",
            status="paid",
        )
        result_dict = json.loads(result)
        
        self.assertTrue(result_dict["updated"])
        
        # The same object should be mutated
        self.assertIs(order1_initial, next((o for o in self.data["orders"] if o["id"] == "order1"), None))
        self.assertEqual(order1_initial["status"], "paid")

    def test_update_order_status_all_fields_preserved(self):
        """Test that other fields in the order are preserved."""
        order1_initial = next((o for o in self.data["orders"] if o["id"] == "order1"), None)
        initial_customer_id = order1_initial["customerId"]
        initial_line_items = order1_initial["lineItems"]
        
        result = UpdateOrderStatus.invoke(
            self.data,
            order_id="order1",
            status="paid",
        )
        result_dict = json.loads(result)
        
        self.assertTrue(result_dict["updated"])
        
        # Other fields should be preserved
        order1 = next((o for o in self.data["orders"] if o["id"] == "order1"), None)
        self.assertEqual(order1["customerId"], initial_customer_id)
        self.assertEqual(order1["lineItems"], initial_line_items)
        self.assertEqual(order1["status"], "paid")

    def test_update_order_status_empty_orders_list(self):
        """Test updating when orders list is empty."""
        empty_data = {"orders": []}
        
        result = UpdateOrderStatus.invoke(
            empty_data,
            order_id="order1",
            status="paid",
        )
        result_dict = json.loads(result)
        
        # Should return updated=False
        self.assertFalse(result_dict["updated"])

    def test_update_order_status_missing_orders_key(self):
        """Test updating when orders key doesn't exist."""
        data_no_orders = {}
        
        result = UpdateOrderStatus.invoke(
            data_no_orders,
            order_id="order1",
            status="paid",
        )
        result_dict = json.loads(result)
        
        # Should return updated=False
        self.assertFalse(result_dict["updated"])

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = UpdateOrderStatus.get_info()
        
        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "updateOrderStatus")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("order_id", info["function"]["parameters"]["properties"])
        self.assertIn("status", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("order_id", required)
        self.assertIn("status", required)


if __name__ == "__main__":
    unittest.main()

