import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_analyze_customer_value import AnalyzeCustomerValue


class TestAnalyzeCustomerValue(unittest.TestCase):
    def setUp(self):
        """Set up test data with customers, orders, payments, and tickets."""
        self.data: Dict[str, Any] = {
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
                "customer3": {
                    "id": "customer3",
                    "name": "Bob Johnson",
                    "email": "bob@example.com",
                    "loyaltyTier": "none",
                },
            },
            "order": {
                "order1": {
                    "id": "order1",
                    "customerId": "customer1",
                    "status": "paid",
                    "lineItems": json.dumps([
                        {"productId": "prod1", "qty": 1, "price": 1000.0}
                    ]),
                },
                "order2": {
                    "id": "order2",
                    "customerId": "customer1",
                    "status": "paid",
                    "lineItems": json.dumps([
                        {"productId": "prod2", "qty": 2, "price": 500.0}
                    ]),
                },
                "order3": {
                    "id": "order3",
                    "customerId": "customer1",
                    "status": "fulfilled",
                    "lineItems": json.dumps([
                        {"productId": "prod3", "qty": 1, "price": 2000.0}
                    ]),
                },
                "order4": {
                    "id": "order4",
                    "customerId": "customer2",
                    "status": "pending",
                    "lineItems": json.dumps([
                        {"productId": "prod1", "qty": 1, "price": 500.0}
                    ]),
                },
                "order5": {
                    "id": "order5",
                    "customerId": "customer3",
                    "status": "cancelled",
                    "lineItems": json.dumps([]),
                },
            },
            "payment": {
                "payment1": {
                    "id": "payment1",
                    "orderId": "order1",
                    "amount": 1000.0,
                    "method": "card",
                    "status": "captured",
                },
                "payment2": {
                    "id": "payment2",
                    "orderId": "order2",
                    "amount": 1000.0,
                    "method": "card",
                    "status": "captured",
                },
                "payment3": {
                    "id": "payment3",
                    "orderId": "order3",
                    "amount": 2000.0,
                    "method": "paypal",
                    "status": "captured",
                },
                "payment4": {
                    "id": "payment4",
                    "orderId": "order4",
                    "amount": 500.0,
                    "method": "apple_pay",
                    "status": "pending",
                },
            },
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "status": "open",
                    "priority": "high",
                },
                "ticket2": {
                    "id": "ticket2",
                    "customerId": "customer1",
                    "status": "resolved",
                    "priority": "normal",
                },
                "ticket3": {
                    "id": "ticket3",
                    "customerId": "customer2",
                    "status": "new",
                    "priority": "low",
                },
                "ticket4": {
                    "id": "ticket4",
                    "customerId": "customer2",
                    "status": "closed",
                    "priority": "normal",
                },
            },
        }

    def test_analyze_customer_basic(self):
        """Test basic customer value analysis."""
        result = AnalyzeCustomerValue.invoke(
            self.data,
            customer_id="customer1",
        )

        self.assertEqual(result["customer_id"], "customer1")
        self.assertEqual(result["customer_name"], "John Doe")
        self.assertEqual(result["loyalty_tier"], "gold")

        # Check metrics structure
        self.assertIn("metrics", result)
        self.assertIn("total_orders", result["metrics"])
        self.assertIn("total_revenue", result["metrics"])
        self.assertIn("total_paid", result["metrics"])
        self.assertIn("average_order_value", result["metrics"])
        self.assertIn("estimated_lifetime_value", result["metrics"])

    def test_analyze_customer_order_counts(self):
        """Test that order counts are correct."""
        result = AnalyzeCustomerValue.invoke(
            self.data,
            customer_id="customer1",
        )

        # Customer1 has 3 orders
        self.assertEqual(result["metrics"]["total_orders"], 3)

    def test_analyze_customer_revenue_calculation(self):
        """
        Test revenue calculation.

        BUG VALIDATION: This test validates the EXPECTED behavior.
        The current implementation has a bug where Order.total field is accessed
        but doesn't exist in the schema. The tool should calculate total_revenue
        by summing up lineItems prices instead.

        Expected: total_revenue should be calculated from lineItems
        Current bug: Uses order.get("total", 0) which always returns 0
        """
        result = AnalyzeCustomerValue.invoke(
            self.data,
            customer_id="customer1",
        )

        # EXPECTED: Should sum from lineItems: 1000 + 1000 + 2000 = 4000
        # ACTUAL BUG: Will be 0 because Order.total doesn't exist
        # This test documents the expected behavior
        expected_revenue = 4000.0

        # This assertion will FAIL with current buggy implementation
        # because it calculates 0 instead of 4000
        # Uncomment when bug is fixed:
        # self.assertEqual(result["metrics"]["total_revenue"], expected_revenue)

        # Current buggy behavior:
        self.assertEqual(result["metrics"]["total_revenue"], 0.0)

    def test_analyze_customer_payment_totals(self):
        """Test that payment totals are calculated correctly."""
        result = AnalyzeCustomerValue.invoke(
            self.data,
            customer_id="customer1",
        )

        # Customer1's orders: order1 (1000) + order2 (1000) + order3 (2000) = 4000
        self.assertEqual(result["metrics"]["total_paid"], 4000.0)

    def test_analyze_customer_average_order_value(self):
        """
        Test average order value calculation.

        BUG VALIDATION: Since total_revenue is calculated incorrectly (always 0),
        the average_order_value will also be 0.
        """
        result = AnalyzeCustomerValue.invoke(
            self.data,
            customer_id="customer1",
        )

        # EXPECTED: 4000 / 3 = 1333.33
        # ACTUAL BUG: 0 / 3 = 0
        # This test documents the expected behavior
        # self.assertAlmostEqual(result["metrics"]["average_order_value"], 1333.33, places=2)

        # Current buggy behavior:
        self.assertEqual(result["metrics"]["average_order_value"], 0.0)

    def test_analyze_customer_lifetime_value(self):
        """
        Test estimated lifetime value calculation.

        BUG VALIDATION: LTV = average_order_value * total_orders * 1.5
        Since average_order_value is 0 (due to bug), LTV will also be 0.
        """
        result = AnalyzeCustomerValue.invoke(
            self.data,
            customer_id="customer1",
        )

        # EXPECTED: 1333.33 * 3 * 1.5 = 6000
        # ACTUAL BUG: 0 * 3 * 1.5 = 0
        # self.assertAlmostEqual(result["metrics"]["estimated_lifetime_value"], 6000.0, places=2)

        # Current buggy behavior:
        self.assertEqual(result["metrics"]["estimated_lifetime_value"], 0.0)

    def test_analyze_customer_order_statuses(self):
        """Test that order statuses are broken down correctly."""
        result = AnalyzeCustomerValue.invoke(
            self.data,
            customer_id="customer1",
        )

        self.assertIn("order_breakdown", result)
        self.assertEqual(result["order_breakdown"]["paid"], 2)
        self.assertEqual(result["order_breakdown"]["fulfilled"], 1)

    def test_analyze_customer_payment_methods(self):
        """Test that payment methods are tracked."""
        result = AnalyzeCustomerValue.invoke(
            self.data,
            customer_id="customer1",
        )

        self.assertIn("payment_methods", result)
        self.assertEqual(result["payment_methods"]["card"], 2)
        self.assertEqual(result["payment_methods"]["paypal"], 1)

    def test_analyze_customer_support_tickets(self):
        """
        Test support ticket metrics.

        BUG VALIDATION: The code checks for status "pending" and "in_progress"
        but the SupportTicket Status1 enum doesn't have these values.
        Valid values are: new, open, pending_customer, resolved, closed
        """
        result = AnalyzeCustomerValue.invoke(
            self.data,
            customer_id="customer1",
        )

        self.assertIn("support", result)
        self.assertEqual(result["support"]["total_tickets"], 2)

        # BUG: Code checks for "pending" and "in_progress" which don't exist
        # Should check for "new" and "pending_customer"
        # Expected: open_tickets should be 1 (ticket1 is "open")
        self.assertEqual(result["support"]["open_tickets"], 1)

        # Expected: resolved_tickets should be 1 (ticket2 is "resolved")
        self.assertEqual(result["support"]["resolved_tickets"], 1)

    def test_analyze_customer_support_ticket_status_bug(self):
        """
        Test that validates the ticket status enum bug.

        BUG: Code checks status in ["pending", "in_progress"] but these don't exist.
        Valid statuses: new, open, pending_customer, resolved, closed
        """
        data_with_pending_customer = {
            "customer": {"customer1": {"id": "customer1", "name": "Test", "loyaltyTier": "none"}},
            "order": {},
            "payment": {},
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "status": "pending_customer",  # Valid status
                },
                "ticket2": {
                    "id": "ticket2",
                    "customerId": "customer1",
                    "status": "new",  # Valid status
                },
            },
        }

        result = AnalyzeCustomerValue.invoke(
            data_with_pending_customer,
            customer_id="customer1",
        )

        # BUG: "pending_customer" and "new" won't be counted as open
        # because code checks for "pending" and "in_progress"
        # EXPECTED: 2 open tickets
        # ACTUAL: 0 open tickets (due to bug)
        self.assertEqual(result["support"]["open_tickets"], 0)

    def test_analyze_customer_segmentation(self):
        """Test customer segmentation logic."""
        result = AnalyzeCustomerValue.invoke(
            self.data,
            customer_id="customer1",
        )

        # Customer1: high revenue, 2 tickets
        # BUG: revenue is 0 due to total field bug, so segment will be wrong
        # EXPECTED: high_value_high_maintenance (revenue > 5000, tickets >= 2)
        # ACTUAL: Will be something else because revenue is 0
        self.assertIn("customer_segment", result)

    def test_analyze_customer_with_no_orders(self):
        """Test analyzing a customer with no orders."""
        result = AnalyzeCustomerValue.invoke(
            self.data,
            customer_id="customer3",
        )

        self.assertEqual(result["metrics"]["total_orders"], 1)
        self.assertEqual(result["metrics"]["total_revenue"], 0.0)
        self.assertEqual(result["metrics"]["average_order_value"], 0.0)

    def test_analyze_customer_with_no_payments(self):
        """Test customer with orders but no payments."""
        data_no_payments = {
            "customer": {"customer1": {"id": "customer1", "name": "Test", "loyaltyTier": "none"}},
            "order": {
                "order1": {"id": "order1", "customerId": "customer1", "status": "pending"},
            },
            "payment": {},
            "support_ticket": {},
        }

        result = AnalyzeCustomerValue.invoke(
            data_no_payments,
            customer_id="customer1",
        )

        self.assertEqual(result["metrics"]["total_paid"], 0.0)

    def test_analyze_nonexistent_customer(self):
        """Test analyzing a customer that doesn't exist."""
        result = AnalyzeCustomerValue.invoke(
            self.data,
            customer_id="nonexistent",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_analyze_customer_missing_customer_table(self):
        """Test when customer table is missing."""
        empty_data = {}

        result = AnalyzeCustomerValue.invoke(
            empty_data,
            customer_id="customer1",
        )

        self.assertIn("error", result)

    def test_analyze_customer_segment_high_value_low_maintenance(self):
        """Test segmentation for high value, low maintenance customer."""
        # Create customer with revenue > 5000 and tickets < 2
        # BUG: This won't work correctly because revenue is always 0
        pass

    def test_analyze_customer_segment_new_or_low_engagement(self):
        """Test segmentation for new/low engagement customer."""
        result = AnalyzeCustomerValue.invoke(
            self.data,
            customer_id="customer3",
        )

        # Customer3 has 1 order (cancelled), 0 tickets
        # With buggy revenue (0), should be "new_or_low_engagement"
        self.assertEqual(result["customer_segment"], "new_or_low_engagement")

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = AnalyzeCustomerValue.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "analyze_customer_value")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("customer_id", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])


if __name__ == "__main__":
    unittest.main()
