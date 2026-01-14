import unittest
from typing import Dict, Any

from ..tau_search_resolutions import SearchResolutions


class TestSearchResolutions(unittest.TestCase):
    def setUp(self):
        """Set up test data with resolutions."""
        self.data: Dict[str, Any] = {
            "resolution": {
                "resolution1": {
                    "id": "resolution1",
                    "ticketId": "tick-001",
                    "outcome": "recommendation_provided",
                    "details": "Recommended HyperVolt DDR5 64GB kit for customer's workstation upgrade.",
                    "createdAt": "2025-09-01T00:00:00Z",
                },
                "resolution2": {
                    "id": "resolution2",
                    "ticketId": "tick-002",
                    "outcome": "order_updated",
                    "details": "Updated shipping address from home to office address as requested.",
                    "resolvedById": "bianca-rossi",
                    "createdAt": "2025-09-02T00:00:00Z",
                },
                "resolution3": {
                    "id": "resolution3",
                    "ticketId": "tick-003",
                    "outcome": "refund_issued",
                    "details": "Customer approved for full refund due to GPU compatibility issue.",
                    "linkedRefundId": "ref-003",
                    "resolvedById": "jordan-lee",
                    "createdAt": "2025-09-03T00:00:00Z",
                },
                "resolution4": {
                    "id": "resolution4",
                    "ticketId": "tick-004",
                    "outcome": "troubleshooting_steps",
                    "details": "Provided GPU temperature troubleshooting steps. Customer confirmed improvement.",
                    "createdAt": "2025-09-04T00:00:00Z",
                },
                "resolution5": {
                    "id": "resolution5",
                    "ticketId": "tick-005",
                    "outcome": "refund_issued",
                    "details": "Partial refund approved for incompatible RAM module.",
                    "linkedRefundId": "ref-005",
                    "resolvedById": "jordan-lee",
                    "createdAt": "2025-09-05T00:00:00Z",
                },
            }
        }

    def test_search_resolutions_no_filters(self):
        """Test searching resolutions with no filters."""
        result_list = SearchResolutions.invoke(self.data)

        # Should return all resolutions (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertEqual(len(result_list), 5)

        # Check structure of first resolution
        if result_list:
            resolution = result_list[0]
            self.assertIn("id", resolution)
            self.assertIn("ticketId", resolution)
            self.assertIn("outcome", resolution)
            self.assertIn("details", resolution)

    def test_search_resolutions_by_resolution_id(self):
        """Test searching resolutions by resolution ID."""
        result_list = SearchResolutions.invoke(
            self.data,
            resolution_id="resolution1",
        )

        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["id"], "resolution1")

    def test_search_resolutions_by_ticket_id(self):
        """Test searching resolutions by ticket ID."""
        result_list = SearchResolutions.invoke(
            self.data,
            ticket_id="tick-002",
        )

        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["ticketId"], "tick-002")

    def test_search_resolutions_by_outcome(self):
        """Test searching resolutions by outcome."""
        result_list = SearchResolutions.invoke(
            self.data,
            outcome="refund_issued",
        )

        self.assertEqual(len(result_list), 2)
        for resolution in result_list:
            self.assertEqual(resolution["outcome"], "refund_issued")

    def test_search_resolutions_by_resolved_by_id(self):
        """Test searching resolutions by resolved_by_id."""
        result_list = SearchResolutions.invoke(
            self.data,
            resolved_by_id="jordan-lee",
        )

        self.assertEqual(len(result_list), 2)
        for resolution in result_list:
            self.assertEqual(resolution["resolvedById"], "jordan-lee")

    def test_search_resolutions_by_linked_refund_id(self):
        """Test searching resolutions by linked refund ID."""
        result_list = SearchResolutions.invoke(
            self.data,
            linked_refund_id="ref-003",
        )

        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["linkedRefundId"], "ref-003")

    def test_search_resolutions_by_details_text(self):
        """Test searching resolutions by details text (case-insensitive)."""
        result_list = SearchResolutions.invoke(
            self.data,
            details_text="GPU",
        )

        self.assertEqual(len(result_list), 2)
        for resolution in result_list:
            self.assertIn("GPU", resolution["details"].upper())

    def test_search_resolutions_by_details_text_case_insensitive(self):
        """Test that details text search is case-insensitive."""
        result_list = SearchResolutions.invoke(
            self.data,
            details_text="gpu",
        )

        self.assertEqual(len(result_list), 2)

    def test_search_resolutions_filter_created_after(self):
        """Test filtering resolutions created after a date."""
        result_list = SearchResolutions.invoke(
            self.data,
            created_after="2025-09-03T00:00:00Z",
        )

        # Should only include resolutions created on or after 2025-09-03
        self.assertEqual(len(result_list), 3)
        for resolution in result_list:
            self.assertGreaterEqual(resolution["createdAt"], "2025-09-03T00:00:00Z")

    def test_search_resolutions_filter_created_before(self):
        """Test filtering resolutions created before a date."""
        result_list = SearchResolutions.invoke(
            self.data,
            created_before="2025-09-02T12:00:00Z",
        )

        # Should only include resolutions created before the date
        self.assertEqual(len(result_list), 2)

    def test_search_resolutions_multiple_filters(self):
        """Test searching with multiple filters."""
        result_list = SearchResolutions.invoke(
            self.data,
            outcome="refund_issued",
            resolved_by_id="jordan-lee",
        )

        # Should match resolutions that satisfy all filters
        self.assertEqual(len(result_list), 2)
        for resolution in result_list:
            self.assertEqual(resolution["outcome"], "refund_issued")
            self.assertEqual(resolution["resolvedById"], "jordan-lee")

    def test_search_resolutions_with_limit(self):
        """Test limiting the number of results."""
        result_list = SearchResolutions.invoke(
            self.data,
            limit=2,
        )

        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_resolutions_limit_max_200(self):
        """Test that limit is capped at 200."""
        result_list = SearchResolutions.invoke(
            self.data,
            limit=500,  # Request more than max
        )

        # Should return at most 200 results
        self.assertLessEqual(len(result_list), 200)

    def test_search_resolutions_default_limit(self):
        """Test that default limit is 50."""
        result_list = SearchResolutions.invoke(self.data)

        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_resolutions_sorted_by_created_at(self):
        """Test that results are sorted by createdAt DESC, then id ASC."""
        result_list = SearchResolutions.invoke(self.data)

        if len(result_list) >= 2:
            # Check that resolutions are sorted by createdAt descending
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

    def test_search_resolutions_no_results(self):
        """Test search with filters that match no resolutions."""
        result_list = SearchResolutions.invoke(
            self.data,
            resolution_id="nonexistent",
        )

        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchResolutions.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "searchResolutions")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("resolution_id", info["function"]["parameters"]["properties"])
        self.assertIn("ticket_id", info["function"]["parameters"]["properties"])
        self.assertIn("outcome", info["function"]["parameters"]["properties"])
        self.assertIn("resolved_by_id", info["function"]["parameters"]["properties"])
        self.assertIn("linked_refund_id", info["function"]["parameters"]["properties"])
        self.assertIn("details_text", info["function"]["parameters"]["properties"])
        self.assertIn("created_after", info["function"]["parameters"]["properties"])
        self.assertIn("created_before", info["function"]["parameters"]["properties"])
        self.assertIn("limit", info["function"]["parameters"]["properties"])
        # All parameters are optional
        self.assertEqual(info["function"]["parameters"].get("required", []), [])


if __name__ == "__main__":
    unittest.main()
