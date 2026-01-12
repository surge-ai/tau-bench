import json
import unittest
from typing import Dict, Any

from ..tau_get_order_details import GetOrderDetails


class TestGetOrderDetails(unittest.TestCase):
    def setUp(self):
        """Set up test data with orders, products, customers, payments, shipments, and tickets."""
        self.data: Dict[str, Any] = {
            "order": {
                "order1": {
                    "id": "order1",
                    "customerId": "customer1",
                    "status": "completed",
                    "lineItems": json.dumps([
                        {"productId": "prod1", "qty": 2, "price": 100.0},
                        {"productId": "prod2", "qty": 1, "price": 200.0},
                    ]),
                    "createdAt": "2025-09-01T00:00:00Z",
                    "updatedAt": "2025-09-01T01:00:00Z",
                },
                "order2": {
                    "id": "order2",
                    "customerId": "customer2",
                    "status": "pending",
                    "lineItems": json.dumps([
                        {"productId": "prod3", "qty": 1, "price": 50.0},
                    ]),
                    "createdAt": "2025-09-02T00:00:00Z",
                    "updatedAt": "2025-09-02T01:00:00Z",
                },
            },
            "customer": {
                "customer1": {
                    "id": "customer1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "loyaltyTier": "gold",
                },
                "customer2": {
                    "id": "customer2",
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "loyaltyTier": "silver",
                },
            },
            "payment": {
                "payment1": {
                    "id": "payment1",
                    "orderId": "order1",
                    "amount": 400.0,
                    "method": "credit_card",
                    "status": "captured",
                    "createdAt": "2025-09-01T00:10:00Z",
                },
            },
            "shipment": {
                "shipment1": {
                    "id": "shipment1",
                    "orderId": "order1",
                    "trackingNumber": "TRACK123",
                    "carrier": "fedex",
                    "status": "delivered",
                    "createdAt": "2025-09-01T00:20:00Z",
                },
            },
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "orderId": "order1",
                    "subject": "Issue with order",
                    "status": "open",
                    "createdAt": "2025-09-01T00:30:00Z",
                },
            },
        }

    def test_get_order_details_basic(self):
        """Test getting details for an existing order."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
        )
        result_dict = json.loads(result)

        self.assertIsNotNone(result_dict)
        self.assertIn("order", result_dict)
        self.assertEqual(result_dict["order"]["id"], "order1")
        self.assertEqual(result_dict["order"]["customer_id"], "customer1")

    def test_get_order_details_nonexistent(self):
        """Test getting details for a non-existent order."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="nonexistent",
        )
        result_dict = json.loads(result)

        # Should return None for order
        self.assertIn("order", result_dict)
        self.assertIsNone(result_dict["order"])

    def test_get_order_details_includes_customer(self):
        """Test that order details includes customer information."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
        )
        result_dict = json.loads(result)

        self.assertIn("customer", result_dict)
        self.assertIsNotNone(result_dict["customer"])
        self.assertEqual(result_dict["customer"]["name"], "John Doe")
        self.assertEqual(result_dict["customer"]["email"], "john@example.com")
        self.assertEqual(result_dict["customer"]["loyalty_tier"], "gold")

    def test_get_order_details_includes_payment(self):
        """Test that order details includes payment information."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
        )
        result_dict = json.loads(result)

        self.assertIn("payment", result_dict)
        self.assertIsNotNone(result_dict["payment"])
        self.assertEqual(result_dict["payment"]["id"], "payment1")
        self.assertEqual(result_dict["payment"]["amount"], 400.0)
        self.assertEqual(result_dict["payment"]["method"], "credit_card")
        self.assertEqual(result_dict["payment"]["status"], "captured")

    def test_get_order_details_includes_shipment(self):
        """Test that order details includes shipment information."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
        )
        result_dict = json.loads(result)

        self.assertIn("shipment", result_dict)
        self.assertIsNotNone(result_dict["shipment"])
        self.assertEqual(result_dict["shipment"]["id"], "shipment1")
        self.assertEqual(result_dict["shipment"]["tracking_number"], "TRACK123")
        self.assertEqual(result_dict["shipment"]["carrier"], "fedex")
        self.assertEqual(result_dict["shipment"]["status"], "delivered")

    def test_get_order_details_includes_tickets(self):
        """Test that order details includes tickets list."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
        )
        result_dict = json.loads(result)

        self.assertIn("tickets", result_dict)
        self.assertIsInstance(result_dict["tickets"], list)
        self.assertEqual(len(result_dict["tickets"]), 1)
        self.assertEqual(result_dict["tickets"][0]["id"], "ticket1")
        self.assertEqual(result_dict["tickets"][0]["subject"], "Issue with order")
        self.assertEqual(result_dict["tickets"][0]["status"], "open")

    def test_get_order_details_parses_line_items(self):
        """Test that line_items JSON is parsed."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
        )
        result_dict = json.loads(result)

        order = result_dict["order"]
        self.assertIn("line_items", order)
        self.assertIsInstance(order["line_items"], list)
        self.assertEqual(len(order["line_items"]), 2)

    def test_get_order_details_missing_order_id(self):
        """Test that missing order_id raises an error."""
        with self.assertRaises(ValueError):
            GetOrderDetails.invoke(
                self.data,
                order_id="",
            )

    def test_get_order_details_none_order_id(self):
        """Test that None order_id raises an error."""
        with self.assertRaises(ValueError):
            GetOrderDetails.invoke(
                self.data,
                order_id=None,
            )

    def test_get_order_details_order_without_payment(self):
        """Test getting details for order without payment."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order2",
        )
        result_dict = json.loads(result)

        self.assertIn("payment", result_dict)
        self.assertIsNone(result_dict["payment"])

    def test_get_order_details_order_without_shipment(self):
        """Test getting details for order without shipment."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order2",
        )
        result_dict = json.loads(result)

        self.assertIn("shipment", result_dict)
        self.assertIsNone(result_dict["shipment"])

    def test_get_order_details_order_without_tickets(self):
        """Test getting details for order without tickets."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order2",
        )
        result_dict = json.loads(result)

        self.assertIn("tickets", result_dict)
        self.assertIsInstance(result_dict["tickets"], list)
        self.assertEqual(len(result_dict["tickets"]), 0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = GetOrderDetails.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "getOrderDetails")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("order_id", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("order_id", info["function"]["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()
