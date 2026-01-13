import json
import unittest
from typing import Dict, Any

from ..tau_search_refunds import SearchRefunds


class TestSearchRefunds(unittest.TestCase):
    def setUp(self):
        """Set up test data with refunds."""
        self.data: Dict[str, Any] = {
            "refund": {
                "refund1": {
                    "id": "refund1",
                    "paymentId": "pay-001",
                    "ticketId": "tick-001",
                    "amount": 79.99,
                    "reason": "customer_remorse",
                    "status": "processed",
                    "lines": [
                        {"sku": "SKU-001", "qty": 1, "amount": 79.99}
                    ],
                    "createdAt": "2025-09-01T00:00:00Z",
                    "processedAt": "2025-09-01T12:00:00Z",
                },
                "refund2": {
                    "id": "refund2",
                    "paymentId": "pay-002",
                    "ticketId": "tick-002",
                    "amount": 199.99,
                    "reason": "defective",
                    "status": "approved",
                    "lines": [
                        {"sku": "SKU-002", "qty": 1, "amount": 199.99}
                    ],
                    "createdAt": "2025-09-02T00:00:00Z",
                    "processedAt": None,
                },
                "refund3": {
                    "id": "refund3",
                    "paymentId": "pay-003",
                    "ticketId": "tick-003",
                    "amount": 149.99,
                    "reason": "incompatible",
                    "status": "processed",
                    "lines": [
                        {"sku": "SKU-003", "qty": 1, "amount": 149.99}
                    ],
                    "createdAt": "2025-09-03T00:00:00Z",
                    "processedAt": "2025-09-03T14:00:00Z",
                },
                "refund4": {
                    "id": "refund4",
                    "paymentId": "pay-001",
                    "ticketId": "tick-004",
                    "amount": 50.00,
                    "reason": "customer_remorse",
                    "status": "pending",
                    "lines": [
                        {"sku": "SKU-004", "qty": 1, "amount": 50.00}
                    ],
                    "createdAt": "2025-09-04T00:00:00Z",
                    "processedAt": None,
                },
            }
        }

    def test_search_refunds_no_filters(self):
        """Test searching refunds with no filters."""
        result = SearchRefunds.invoke(self.data)
        result_list = json.loads(result)

        # Should return all refunds (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertEqual(len(result_list), 4)

        # Check structure of first refund
        if result_list:
            refund = result_list[0]
            self.assertIn("id", refund)
            self.assertIn("paymentId", refund)
            self.assertIn("ticketId", refund)
            self.assertIn("reason", refund)
            self.assertIn("status", refund)

    def test_search_refunds_by_refund_id(self):
        """Test searching refunds by refund ID."""
        result = SearchRefunds.invoke(
            self.data,
            refund_id="refund1",
        )
        result_list = json.loads(result)

        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["id"], "refund1")

    def test_search_refunds_by_payment_id(self):
        """Test searching refunds by payment ID."""
        result = SearchRefunds.invoke(
            self.data,
            payment_id="pay-001",
        )
        result_list = json.loads(result)

        # Should return refunds for pay-001
        self.assertEqual(len(result_list), 2)
        for refund in result_list:
            self.assertEqual(refund["paymentId"], "pay-001")

    def test_search_refunds_by_ticket_id(self):
        """Test searching refunds by ticket ID."""
        result = SearchRefunds.invoke(
            self.data,
            ticket_id="tick-002",
        )
        result_list = json.loads(result)

        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["ticketId"], "tick-002")

    def test_search_refunds_by_reason(self):
        """Test searching refunds by reason."""
        result = SearchRefunds.invoke(
            self.data,
            reason="customer_remorse",
        )
        result_list = json.loads(result)

        self.assertEqual(len(result_list), 2)
        for refund in result_list:
            self.assertEqual(refund["reason"], "customer_remorse")

    def test_search_refunds_by_status(self):
        """Test searching refunds by status."""
        result = SearchRefunds.invoke(
            self.data,
            status="processed",
        )
        result_list = json.loads(result)

        self.assertEqual(len(result_list), 2)
        for refund in result_list:
            self.assertEqual(refund["status"], "processed")

    def test_search_refunds_filter_created_after(self):
        """Test filtering refunds created after a date."""
        result = SearchRefunds.invoke(
            self.data,
            created_after="2025-09-02T00:00:00Z",
        )
        result_list = json.loads(result)

        # Should only include refunds created on or after 2025-09-02
        self.assertEqual(len(result_list), 3)
        for refund in result_list:
            self.assertGreaterEqual(refund["createdAt"], "2025-09-02T00:00:00Z")

    def test_search_refunds_filter_created_before(self):
        """Test filtering refunds created before a date."""
        result = SearchRefunds.invoke(
            self.data,
            created_before="2025-09-02T12:00:00Z",
        )
        result_list = json.loads(result)

        # Should only include refunds created before the date
        self.assertEqual(len(result_list), 2)

    def test_search_refunds_filter_processed_after(self):
        """Test filtering refunds processed after a date."""
        result = SearchRefunds.invoke(
            self.data,
            processed_after="2025-09-01T10:00:00Z",
        )
        result_list = json.loads(result)

        # Should only include refunds processed on or after the date (excludes None processedAt)
        self.assertEqual(len(result_list), 2)
        for refund in result_list:
            self.assertIsNotNone(refund.get("processedAt"))
            self.assertGreaterEqual(refund["processedAt"], "2025-09-01T10:00:00Z")

    def test_search_refunds_filter_processed_before(self):
        """Test filtering refunds processed before a date."""
        result = SearchRefunds.invoke(
            self.data,
            processed_before="2025-09-02T00:00:00Z",
        )
        result_list = json.loads(result)

        # Should only include refunds processed before the date
        self.assertEqual(len(result_list), 1)

    def test_search_refunds_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchRefunds.invoke(
            self.data,
            reason="customer_remorse",
            status="processed",
        )
        result_list = json.loads(result)

        # Should match refunds that satisfy all filters
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["reason"], "customer_remorse")
        self.assertEqual(result_list[0]["status"], "processed")

    def test_search_refunds_with_limit(self):
        """Test limiting the number of results."""
        result = SearchRefunds.invoke(
            self.data,
            limit=2,
        )
        result_list = json.loads(result)

        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_refunds_limit_max_200(self):
        """Test that limit is capped at 200."""
        result = SearchRefunds.invoke(
            self.data,
            limit=500,  # Request more than max
        )
        result_list = json.loads(result)

        # Should return at most 200 results
        self.assertLessEqual(len(result_list), 200)

    def test_search_refunds_default_limit(self):
        """Test that default limit is 50."""
        result = SearchRefunds.invoke(self.data)
        result_list = json.loads(result)

        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_refunds_sorted_by_created_at(self):
        """Test that results are sorted by createdAt DESC, then id ASC."""
        result = SearchRefunds.invoke(self.data)
        result_list = json.loads(result)

        if len(result_list) >= 2:
            # Check that refunds are sorted by createdAt descending
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

    def test_search_refunds_no_results(self):
        """Test search with filters that match no refunds."""
        result = SearchRefunds.invoke(
            self.data,
            refund_id="nonexistent",
        )
        result_list = json.loads(result)

        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchRefunds.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "searchRefunds")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("refund_id", info["function"]["parameters"]["properties"])
        self.assertIn("payment_id", info["function"]["parameters"]["properties"])
        self.assertIn("ticket_id", info["function"]["parameters"]["properties"])
        self.assertIn("reason", info["function"]["parameters"]["properties"])
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
