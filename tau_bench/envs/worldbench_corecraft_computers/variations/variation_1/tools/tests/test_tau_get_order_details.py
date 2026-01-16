import json
import unittest
from typing import Dict, Any

from ..tau_get_order_details import GetOrderDetails


class TestGetOrderDetails(unittest.TestCase):
    def setUp(self):
        """Set up test data with orders, payments, shipments, customers, and tickets."""
        self.data: Dict[str, Any] = {
            "order": {
                "order1": {
                    "id": "order1",
                    "customerId": "customer1",
                    "status": "paid",
                    "lineItems": json.dumps([
                        {"productId": "prod1", "qty": 1, "price": 100.0}
                    ]),
                    "shipping": json.dumps({
                        "carrier": "FedEx",
                        "service": "express"
                    }),
                    "createdAt": "2025-09-01T00:00:00Z",
                    "updatedAt": "2025-09-01T01:00:00Z",
                },
                "order2": {
                    "id": "order2",
                    "customerId": "customer2",
                    "status": "pending",
                    "lineItems": json.dumps([
                        {"productId": "prod2", "qty": 2, "price": 50.0}
                    ]),
                    "shipping": json.dumps({
                        "carrier": "UPS",
                        "service": "ground"
                    }),
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
                    "amount": 100.0,
                    "method": "card",
                    "status": "captured",
                    "createdAt": "2025-09-01T00:10:00Z",
                },
                "payment2": {
                    "id": "payment2",
                    "orderId": "order1",
                    "amount": 150.0,
                    "method": "card",
                    "status": "refunded",
                    "createdAt": "2025-09-01T00:20:00Z",
                },
                "payment3": {
                    "id": "payment3",
                    "orderId": "order2",
                    "amount": 100.0,
                    "method": "paypal",
                    "status": "pending",
                    "createdAt": "2025-09-02T00:10:00Z",
                },
            },
            "shipment": {
                "shipment1": {
                    "id": "shipment1",
                    "orderId": "order1",
                    "trackingNumber": "TRACK123",
                    "carrier": "FedEx",
                    "status": "in_transit",
                    "createdAt": "2025-09-01T00:15:00Z",
                },
                "shipment2": {
                    "id": "shipment2",
                    "orderId": "order1",
                    "trackingNumber": "TRACK456",
                    "carrier": "UPS",
                    "status": "delivered",
                    "createdAt": "2025-09-01T00:25:00Z",
                },
                "shipment3": {
                    "id": "shipment3",
                    "orderId": "order2",
                    "trackingNumber": "TRACK789",
                    "carrier": "USPS",
                    "status": "pending",
                    "createdAt": "2025-09-02T00:15:00Z",
                },
            },
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "orderId": "order1",
                    "subject": "Order question",
                    "status": "open",
                    "createdAt": "2025-09-01T00:30:00Z",
                },
                "ticket2": {
                    "id": "ticket2",
                    "orderId": "order1",
                    "subject": "Shipping inquiry",
                    "status": "resolved",
                    "createdAt": "2025-09-01T00:40:00Z",
                },
            },
        }

    def test_get_order_details_basic(self):
        """Test getting order details for an existing order."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
        )
        result_dict = result

        # Check structure
        self.assertIn("order", result_dict)
        self.assertIn("payment", result_dict)
        self.assertIn("shipment", result_dict)
        self.assertIn("customer", result_dict)
        self.assertIn("tickets", result_dict)

        # Check order details
        order = result_dict["order"]
        self.assertIsNotNone(order)
        self.assertEqual(order["id"], "order1")
        self.assertEqual(order["customer_id"], "customer1")
        self.assertEqual(order["status"], "paid")
        self.assertIn("line_items", order)
        self.assertIn("created_at", order)
        self.assertIn("updated_at", order)

    def test_get_order_details_nonexistent_order(self):
        """Test getting details for non-existent order raises ValueError."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="nonexistent",
        )
        self.assertIn("error", result)
        self.assertIn("nonexistent", result["error"])

    def test_get_order_details_includes_customer(self):
        """Test that customer information is included."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
        )
        result_dict = result

        customer = result_dict["customer"]
        self.assertIsNotNone(customer)
        self.assertEqual(customer["name"], "John Doe")
        self.assertEqual(customer["email"], "john@example.com")
        self.assertEqual(customer["loyalty_tier"], "gold")

    def test_get_order_details_most_recent_payment(self):
        """Test that most recent payment is returned."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
        )
        result_dict = result

        payment = result_dict["payment"]
        self.assertIsNotNone(payment)
        # Should be payment2 (most recent - created at 00:20:00)
        self.assertEqual(payment["id"], "payment2")
        self.assertEqual(payment["amount"], 150.0)
        self.assertEqual(payment["status"], "refunded")

    def test_get_order_details_most_recent_shipment(self):
        """Test that most recent shipment is returned."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
        )
        result_dict = result

        shipment = result_dict["shipment"]
        self.assertIsNotNone(shipment)
        # Should be shipment2 (most recent - created at 00:25:00)
        self.assertEqual(shipment["id"], "shipment2")
        self.assertEqual(shipment["tracking_number"], "TRACK456")
        self.assertEqual(shipment["status"], "delivered")

    def test_get_order_details_includes_tickets(self):
        """Test that tickets are included."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
        )
        result_dict = result

        tickets = result_dict["tickets"]
        self.assertIsInstance(tickets, list)
        self.assertEqual(len(tickets), 2)

        # Check ticket structure
        ticket = tickets[0]
        self.assertIn("id", ticket)
        self.assertIn("subject", ticket)
        self.assertIn("status", ticket)

        # Check both tickets are present
        ticket_ids = [t["id"] for t in tickets]
        self.assertIn("ticket1", ticket_ids)
        self.assertIn("ticket2", ticket_ids)

    def test_get_order_details_filtered_by_created_before(self):
        """Test filtering by created_before date."""
        # Filter to only include items created before 00:18:00
        # This should include payment1 (00:10:00) but not payment2 (00:20:00)
        # This should include shipment1 (00:15:00) but not shipment2 (00:25:00)
        # This should exclude both tickets (00:30:00 and 00:40:00)
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
            created_before="2025-09-01T00:18:00Z",
        )
        result_dict = result

        # Order should still be returned
        self.assertIsNotNone(result_dict["order"])
        self.assertEqual(result_dict["order"]["id"], "order1")

        # Payment should be payment1 (only one before cutoff)
        payment = result_dict["payment"]
        self.assertIsNotNone(payment)
        self.assertEqual(payment["id"], "payment1")
        self.assertEqual(payment["amount"], 100.0)

        # Shipment should be shipment1 (only one before cutoff)
        shipment = result_dict["shipment"]
        self.assertIsNotNone(shipment)
        self.assertEqual(shipment["id"], "shipment1")
        self.assertEqual(shipment["tracking_number"], "TRACK123")

        # Tickets should be empty (both after cutoff)
        self.assertEqual(len(result_dict["tickets"]), 0)

    def test_get_order_details_parses_json_fields(self):
        """Test that JSON fields in order are parsed."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
        )
        result_dict = result

        order = result_dict["order"]
        # line_items should be parsed from JSON string
        self.assertIsInstance(order["line_items"], list)
        self.assertEqual(len(order["line_items"]), 1)
        self.assertIsInstance(order["line_items"][0], dict)
        self.assertEqual(order["line_items"][0]["productId"], "prod1")

    def test_get_order_details_missing_order_id(self):
        """Test that missing order_id raises an error."""
        result = GetOrderDetails.invoke(
                self.data,
                order_id="",
)

        self.assertIn("error", result)

    def test_get_order_details_none_order_id(self):
        """Test that None order_id raises an error."""
        result = GetOrderDetails.invoke(
                self.data,
                order_id=None,
)

        self.assertIn("error", result)

    def test_get_order_details_date_format(self):
        """Test that dates are in correct format."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
        )
        result_dict = result

        order = result_dict["order"]
        # Dates should be ISO format
        self.assertRegex(order["created_at"], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')
        self.assertRegex(order["updated_at"], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = GetOrderDetails.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "getOrderDetails")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("order_id", info["function"]["parameters"]["properties"])
        self.assertIn("created_before", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("order_id", info["function"]["parameters"]["required"])

    # Additional tests from current branch

    def test_get_order_details_order_without_payment(self):
        """Test getting details for order without payment."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order2",
        )
        result_dict = result

        # order2 has payment3, so payment should not be None
        # Let's create a test with an order that has no payments
        data_no_payment = {
            "order": {
                "order_no_payment": {
                    "id": "order_no_payment",
                    "customerId": "customer1",
                    "status": "pending",
                    "lineItems": json.dumps([]),
                    "createdAt": "2025-09-01T00:00:00Z",
                    "updatedAt": "2025-09-01T00:00:00Z",
                }
            },
            "customer": {
                "customer1": {
                    "id": "customer1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "loyaltyTier": "gold",
                }
            },
            "payment": {},
            "shipment": {},
            "support_ticket": {},
        }
        result = GetOrderDetails.invoke(
            data_no_payment,
            order_id="order_no_payment",
        )
        result_dict = result

        self.assertIn("payment", result_dict)
        self.assertIsNone(result_dict["payment"])

    def test_get_order_details_order_without_shipment(self):
        """Test getting details for order without shipment."""
        data_no_shipment = {
            "order": {
                "order_no_shipment": {
                    "id": "order_no_shipment",
                    "customerId": "customer1",
                    "status": "pending",
                    "lineItems": json.dumps([]),
                    "createdAt": "2025-09-01T00:00:00Z",
                    "updatedAt": "2025-09-01T00:00:00Z",
                }
            },
            "customer": {
                "customer1": {
                    "id": "customer1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "loyaltyTier": "gold",
                }
            },
            "payment": {},
            "shipment": {},
            "support_ticket": {},
        }
        result = GetOrderDetails.invoke(
            data_no_shipment,
            order_id="order_no_shipment",
        )
        result_dict = result

        self.assertIn("shipment", result_dict)
        self.assertIsNone(result_dict["shipment"])

    def test_get_order_details_order_without_tickets(self):
        """Test getting details for order without tickets."""
        data_no_tickets = {
            "order": {
                "order_no_tickets": {
                    "id": "order_no_tickets",
                    "customerId": "customer1",
                    "status": "pending",
                    "lineItems": json.dumps([]),
                    "createdAt": "2025-09-01T00:00:00Z",
                    "updatedAt": "2025-09-01T00:00:00Z",
                }
            },
            "customer": {
                "customer1": {
                    "id": "customer1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "loyaltyTier": "gold",
                }
            },
            "payment": {},
            "shipment": {},
            "support_ticket": {},
        }
        result = GetOrderDetails.invoke(
            data_no_tickets,
            order_id="order_no_tickets",
        )
        result_dict = result

        self.assertIn("tickets", result_dict)
        self.assertIsInstance(result_dict["tickets"], list)
        self.assertEqual(len(result_dict["tickets"]), 0)

    def test_get_order_details_order_without_customer(self):
        """Test getting details for order with missing customer."""
        data_missing_customer = {
            "order": {
                "order_missing_cust": {
                    "id": "order_missing_cust",
                    "customerId": "nonexistent_customer",
                    "status": "pending",
                    "lineItems": json.dumps([]),
                    "createdAt": "2025-09-01T00:00:00Z",
                    "updatedAt": "2025-09-01T00:00:00Z",
                }
            },
            "customer": {},
            "payment": {},
            "shipment": {},
            "support_ticket": {},
        }
        result = GetOrderDetails.invoke(
            data_missing_customer,
            order_id="order_missing_cust",
        )
        result_dict = result

        # Customer should be None since the customerId doesn't exist
        self.assertIn("customer", result_dict)
        self.assertIsNone(result_dict["customer"])

    def test_get_order_details_tickets_sorted(self):
        """Test that tickets are sorted by createdAt DESC, then id ASC."""
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
        )
        result_dict = result

        tickets = result_dict["tickets"]
        self.assertEqual(len(tickets), 2)

        # ticket2 is newer (00:40:00) so should be first
        self.assertEqual(tickets[0]["id"], "ticket2")
        self.assertEqual(tickets[1]["id"], "ticket1")

    def test_get_order_details_created_before_excludes_all_related(self):
        """Test that created_before can exclude all related entities."""
        # Use a time before any payments, shipments, or tickets
        result = GetOrderDetails.invoke(
            self.data,
            order_id="order1",
            created_before="2025-09-01T00:05:00Z",
        )
        result_dict = result

        # Order should still be returned
        self.assertIsNotNone(result_dict["order"])

        # All related entities should be filtered out
        self.assertIsNone(result_dict["payment"])
        self.assertIsNone(result_dict["shipment"])
        self.assertEqual(len(result_dict["tickets"]), 0)


if __name__ == "__main__":
    unittest.main()
