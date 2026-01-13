import unittest
from typing import Dict, Any

from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tools.tau_update_order_status import UpdateOrderStatus


class TestUpdateOrderStatus(unittest.TestCase):
    def setUp(self):
        """Set up test data with orders."""
        self.data: Dict[str, Any] = {
            "order": {
                "order1": {
                    "id": "order1",
                    "customerId": "customer1",
                    "status": "pending",
                    "lineItems": [
                        {"productId": "prod1", "qty": 1, "price": 100.0}
                    ],
                },
                "order2": {
                    "id": "order2",
                    "customerId": "customer1",
                    "status": "paid",
                    "lineItems": [
                        {"productId": "prod2", "qty": 2, "price": 50.0}
                    ],
                },
                "order3": {
                    "id": "order3",
                    "customerId": "customer2",
                    "status": "pending",
                    "lineItems": [
                        {"productId": "prod3", "qty": 1, "price": 200.0}
                    ],
                },
            }
        }

    def test_update_order_status_basic(self):
        """Test updating order status."""
        result_dict = UpdateOrderStatus.invoke(
            self.data,
            order_id="order1",
            status="paid",
        )

        # Should return the updated order
        self.assertEqual(result_dict["id"], "order1")
        self.assertEqual(result_dict["status"], "paid")

        # Should mutate data in place
        self.assertEqual(self.data["order"]["order1"]["status"], "paid")

    def test_update_order_status_different_statuses(self):
        """Test updating to different status values."""
        statuses = ["paid", "fulfilled", "cancelled", "backorder", "refunded"]

        for status in statuses:
            # Reset order1 status
            self.data["order"]["order1"]["status"] = "pending"

            result_dict = UpdateOrderStatus.invoke(
                self.data,
                order_id="order1",
                status=status,
            )

            self.assertEqual(result_dict["status"], status)
            self.assertEqual(self.data["order"]["order1"]["status"], status)

    def test_update_order_status_nonexistent_order(self):
        """Test updating non-existent order raises ValueError."""
        with self.assertRaises(ValueError) as context:
            UpdateOrderStatus.invoke(
                self.data,
                order_id="nonexistent",
                status="paid",
            )

        self.assertIn("nonexistent", str(context.exception))
        self.assertIn("not found", str(context.exception))

        # Data should not be changed
        self.assertEqual(len(self.data["order"]), 3)

    def test_update_order_status_multiple_updates(self):
        """Test updating the same order multiple times."""
        # First update
        result_dict1 = UpdateOrderStatus.invoke(
            self.data,
            order_id="order1",
            status="paid",
        )

        self.assertEqual(result_dict1["status"], "paid")
        self.assertEqual(self.data["order"]["order1"]["status"], "paid")

        # Second update
        result_dict2 = UpdateOrderStatus.invoke(
            self.data,
            order_id="order1",
            status="fulfilled",
        )

        self.assertEqual(result_dict2["status"], "fulfilled")
        self.assertEqual(self.data["order"]["order1"]["status"], "fulfilled")

    def test_update_order_status_other_orders_unchanged(self):
        """Test that other orders are not affected."""
        initial_status_order2 = self.data["order"]["order2"]["status"]

        result_dict = UpdateOrderStatus.invoke(
            self.data,
            order_id="order1",
            status="paid",
        )

        self.assertEqual(result_dict["status"], "paid")

        # order2 should be unchanged
        self.assertEqual(self.data["order"]["order2"]["status"], initial_status_order2)

        # order3 should be unchanged
        self.assertEqual(self.data["order"]["order3"]["status"], "pending")

    def test_update_order_status_mutates_data_in_place(self):
        """Test that the tool mutates data in place (write tool behavior)."""
        # Get initial reference to order
        order1_initial = self.data["order"]["order1"]
        self.assertIsNotNone(order1_initial)

        result_dict = UpdateOrderStatus.invoke(
            self.data,
            order_id="order1",
            status="paid",
        )

        self.assertEqual(result_dict["status"], "paid")

        # The same object should be mutated
        self.assertIs(order1_initial, self.data["order"]["order1"])
        self.assertEqual(order1_initial["status"], "paid")

    def test_update_order_status_all_fields_preserved(self):
        """Test that other fields in the order are preserved."""
        order1_initial = self.data["order"]["order1"]
        initial_customer_id = order1_initial["customerId"]
        initial_line_items = order1_initial["lineItems"]

        result_dict = UpdateOrderStatus.invoke(
            self.data,
            order_id="order1",
            status="paid",
        )

        self.assertEqual(result_dict["status"], "paid")
        self.assertEqual(result_dict["customerId"], initial_customer_id)
        self.assertEqual(result_dict["lineItems"], initial_line_items)

        # Other fields should be preserved in data
        self.assertEqual(self.data["order"]["order1"]["customerId"], initial_customer_id)
        self.assertEqual(self.data["order"]["order1"]["lineItems"], initial_line_items)
        self.assertEqual(self.data["order"]["order1"]["status"], "paid")

    def test_update_order_status_empty_orders(self):
        """Test updating when orders dict is empty raises ValueError."""
        empty_data = {"order": {}}

        with self.assertRaises(ValueError) as context:
            UpdateOrderStatus.invoke(
                empty_data,
                order_id="order1",
                status="paid",
            )

        self.assertIn("not found", str(context.exception))

    def test_update_order_status_missing_orders_key(self):
        """Test updating when order key doesn't exist raises ValueError."""
        data_no_orders = {}

        with self.assertRaises(ValueError) as context:
            UpdateOrderStatus.invoke(
                data_no_orders,
                order_id="order1",
                status="paid",
            )

        self.assertIn("table not found", str(context.exception).lower())

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
