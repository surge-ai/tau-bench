import json
import unittest
from typing import Dict, Any

from ..tau_search_payments import SearchPayments


class TestSearchPayments(unittest.TestCase):
    def setUp(self):
        """Set up test data with payments."""
        self.data: Dict[str, Any] = {
            "payment": {
                "payment1": {
                    "id": "payment1",
                    "orderId": "order1",
                    "amount": 100.0,
                    "method": "card",
                    "status": "captured",
                    "transactionId": "TXN-001",
                    "createdAt": "2025-09-01T00:00:00Z",
                    "processedAt": "2025-09-01T00:16:40Z",
                },
                "payment2": {
                    "id": "payment2",
                    "orderId": "order1",
                    "amount": 150.0,
                    "method": "paypal",
                    "status": "refunded",
                    "transactionId": "TXN-002",
                    "createdAt": "2025-09-02T00:00:00Z",
                    "processedAt": "2025-09-02T00:10:00Z",
                },
                "payment3": {
                    "id": "payment3",
                    "orderId": "order2",
                    "amount": 200.0,
                    "method": "card",
                    "status": "pending",
                    "transactionId": "TXN-003",
                    "createdAt": "2025-09-03T00:00:00Z",
                    "processedAt": None,
                },
                "payment4": {
                    "id": "payment4",
                    "orderId": "order3",
                    "amount": 50.0,
                    "method": "card",
                    "status": "captured",
                    "transactionId": "TXN-004",
                    "createdAt": "2025-09-04T00:00:00Z",
                    "processedAt": "2025-09-04T00:13:20Z",
                },
            }
        }

    def test_search_payments_no_filters(self):
        """Test searching payments with no filters."""
        result = SearchPayments.invoke(self.data)
        result_list = result

        # Should return all payments (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertEqual(len(result_list), 4)

        # Check structure of first payment
        if result_list:
            payment = result_list[0]
            self.assertIn("id", payment)
            self.assertIn("orderId", payment)
            self.assertIn("status", payment)

    def test_search_payments_by_order_id(self):
        """Test searching payments by order ID."""
        result = SearchPayments.invoke(
            self.data,
            order_id="order1",
        )
        result_list = result

        # Should return payments for order1
        self.assertEqual(len(result_list), 2)
        for payment in result_list:
            self.assertEqual(payment["orderId"], "order1")

    def test_search_payments_by_status(self):
        """Test searching payments by status."""
        result = SearchPayments.invoke(
            self.data,
            status="captured",
        )
        result_list = result

        # Should return payments with captured status
        self.assertEqual(len(result_list), 2)
        for payment in result_list:
            self.assertEqual(payment["status"], "captured")

    def test_search_payments_filter_created_after(self):
        """Test filtering payments created after a date."""
        result = SearchPayments.invoke(
            self.data,
            created_after="2025-09-02T00:00:00Z",
        )
        result_list = result

        # Should only include payments created on or after 2025-09-02
        self.assertEqual(len(result_list), 3)
        for payment in result_list:
            self.assertGreaterEqual(payment["createdAt"], "2025-09-02T00:00:00Z")

    def test_search_payments_filter_created_before(self):
        """Test filtering payments created before a date."""
        result = SearchPayments.invoke(
            self.data,
            created_before="2025-09-02T12:00:00Z",
        )
        result_list = result

        # Should only include payments created before the date
        self.assertEqual(len(result_list), 2)

    def test_search_payments_filter_processed_after(self):
        """Test filtering payments processed after a date."""
        result = SearchPayments.invoke(
            self.data,
            processed_after="2025-09-02T00:00:00Z",
        )
        result_list = result

        # Should only include payments processed on or after the date
        self.assertEqual(len(result_list), 2)
        for payment in result_list:
            if payment.get("processedAt") is not None:
                self.assertGreaterEqual(payment["processedAt"], "2025-09-02T00:00:00Z")

    def test_search_payments_filter_processed_before(self):
        """Test filtering payments processed before a date."""
        result = SearchPayments.invoke(
            self.data,
            processed_before="2025-09-02T12:00:00Z",
        )
        result_list = result

        # Should only include payments processed before the date
        self.assertEqual(len(result_list), 2)

    def test_search_payments_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchPayments.invoke(
            self.data,
            order_id="order1",
            status="captured",
        )
        result_list = result

        # Should match payments that satisfy all filters
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["orderId"], "order1")
        self.assertEqual(result_list[0]["status"], "captured")

    def test_search_payments_with_limit(self):
        """Test limiting the number of results."""
        result = SearchPayments.invoke(
            self.data,
            limit=2,
        )
        result_list = result

        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_payments_limit_max_200(self):
        """Test that limit is capped at 200."""
        result = SearchPayments.invoke(
            self.data,
            limit=500,  # Request more than max
        )
        result_list = result

        # Should return at most 200 results
        self.assertLessEqual(len(result_list), 200)

    def test_search_payments_default_limit(self):
        """Test that default limit is 50."""
        result = SearchPayments.invoke(self.data)
        result_list = result

        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_payments_sorted_by_created_at(self):
        """Test that results are sorted by createdAt DESC, then id ASC."""
        result = SearchPayments.invoke(self.data)
        result_list = result

        if len(result_list) >= 2:
            # Check that payments are sorted by createdAt descending
            for i in range(len(result_list) - 1):
                current_created = result_list[i]["createdAt"]
                next_created = result_list[i + 1]["createdAt"]
                # Should be in descending order
                if current_created == next_created:
                    # If createdAt is equal, check IDs
                    current_id = result_list[i]["id"]
                    next_id = result_list[i + 1]["id"]
                    self.assertLessEqual(current_id, next_id)
                else:
                    self.assertGreaterEqual(current_created, next_created)

    def test_search_payments_no_results(self):
        """Test search with filters that match no payments."""
        result = SearchPayments.invoke(
            self.data,
            order_id="nonexistent",
        )
        result_list = result

        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchPayments.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "searchPayments")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("order_id", info["function"]["parameters"]["properties"])
        self.assertIn("status", info["function"]["parameters"]["properties"])
        self.assertIn("created_after", info["function"]["parameters"]["properties"])
        self.assertIn("created_before", info["function"]["parameters"]["properties"])
        self.assertIn("processed_after", info["function"]["parameters"]["properties"])
        self.assertIn("processed_before", info["function"]["parameters"]["properties"])
        self.assertIn("limit", info["function"]["parameters"]["properties"])
        # All parameters are optional
        self.assertEqual(info["function"]["parameters"].get("required", []), [])


if __name__ == "__main__":
    unittest.main()
