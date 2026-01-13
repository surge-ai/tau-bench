import unittest
from typing import Dict, Any

from ..tau_search_escalations import SearchEscalations


class TestSearchEscalations(unittest.TestCase):
    def setUp(self):
        """Set up test data with escalations."""
        self.data: Dict[str, Any] = {
            "escalation": {
                "escalation1": {
                    "id": "escalation1",
                    "ticketId": "tick-001",
                    "escalationType": "product_specialist",
                    "destination": "product_management",
                    "notes": "Customer compatibility miss highlights need for better GPU case clearance warnings.",
                    "createdAt": "2025-09-01T00:00:00Z",
                    "resolvedAt": "2025-09-01T14:00:00Z",
                },
                "escalation2": {
                    "id": "escalation2",
                    "ticketId": "tick-002",
                    "escalationType": "policy_exception",
                    "destination": "operations",
                    "notes": "Warehouse fulfillment error - customer ordered wrong item. Need expedited replacement.",
                    "createdAt": "2025-09-02T00:00:00Z",
                    "resolvedAt": None,
                },
                "escalation3": {
                    "id": "escalation3",
                    "ticketId": "tick-003",
                    "escalationType": "technical",
                    "destination": "engineering",
                    "notes": "Complex no-boot issue with custom build. Need advanced diagnostics.",
                    "createdAt": "2025-09-03T00:00:00Z",
                    "resolvedAt": "2025-09-03T16:00:00Z",
                },
                "escalation4": {
                    "id": "escalation4",
                    "ticketId": "tick-004",
                    "escalationType": "product_specialist",
                    "destination": "product_management",
                    "notes": "Multiple customer reports of GPU clearance issues. Escalating for product page updates.",
                    "createdAt": "2025-09-04T00:00:00Z",
                    "resolvedAt": None,
                },
            }
        }

    def test_search_escalations_no_filters(self):
        """Test searching escalations with no filters."""
        result_list = SearchEscalations.invoke(self.data)

        # Should return all escalations (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertEqual(len(result_list), 4)

        # Check structure of first escalation
        if result_list:
            escalation = result_list[0]
            self.assertIn("id", escalation)
            self.assertIn("ticketId", escalation)
            self.assertIn("escalationType", escalation)
            self.assertIn("destination", escalation)
            self.assertIn("notes", escalation)

    def test_search_escalations_by_escalation_id(self):
        """Test searching escalations by escalation ID."""
        result_list = SearchEscalations.invoke(
            self.data,
            escalation_id="escalation1",
        )

        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["id"], "escalation1")

    def test_search_escalations_by_ticket_id(self):
        """Test searching escalations by ticket ID."""
        result_list = SearchEscalations.invoke(
            self.data,
            ticket_id="tick-002",
        )

        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["ticketId"], "tick-002")

    def test_search_escalations_by_escalation_type(self):
        """Test searching escalations by escalation type."""
        result_list = SearchEscalations.invoke(
            self.data,
            escalation_type="product_specialist",
        )

        self.assertEqual(len(result_list), 2)
        for escalation in result_list:
            self.assertEqual(escalation["escalationType"], "product_specialist")

    def test_search_escalations_by_destination(self):
        """Test searching escalations by destination."""
        result_list = SearchEscalations.invoke(
            self.data,
            destination="product_management",
        )

        self.assertEqual(len(result_list), 2)
        for escalation in result_list:
            self.assertEqual(escalation["destination"], "product_management")

    def test_search_escalations_by_notes_text(self):
        """Test searching escalations by notes text (case-insensitive)."""
        result_list = SearchEscalations.invoke(
            self.data,
            notes_text="GPU",
        )

        self.assertEqual(len(result_list), 2)
        for escalation in result_list:
            self.assertIn("GPU", escalation["notes"].upper())

    def test_search_escalations_by_notes_text_case_insensitive(self):
        """Test that notes text search is case-insensitive."""
        result_list = SearchEscalations.invoke(
            self.data,
            notes_text="gpu",
        )

        self.assertEqual(len(result_list), 2)

    def test_search_escalations_filter_created_after(self):
        """Test filtering escalations created after a date."""
        result_list = SearchEscalations.invoke(
            self.data,
            created_after="2025-09-02T00:00:00Z",
        )

        # Should only include escalations created on or after 2025-09-02
        self.assertEqual(len(result_list), 3)
        for escalation in result_list:
            self.assertGreaterEqual(escalation["createdAt"], "2025-09-02T00:00:00Z")

    def test_search_escalations_filter_created_before(self):
        """Test filtering escalations created before a date."""
        result_list = SearchEscalations.invoke(
            self.data,
            created_before="2025-09-02T12:00:00Z",
        )

        # Should only include escalations created before the date
        self.assertEqual(len(result_list), 2)

    def test_search_escalations_filter_resolved_after(self):
        """Test filtering escalations resolved after a date."""
        result_list = SearchEscalations.invoke(
            self.data,
            resolved_after="2025-09-01T10:00:00Z",
        )

        # Should only include escalations resolved on or after the date (excludes None resolvedAt)
        self.assertEqual(len(result_list), 2)
        for escalation in result_list:
            self.assertIsNotNone(escalation.get("resolvedAt"))
            self.assertGreaterEqual(escalation["resolvedAt"], "2025-09-01T10:00:00Z")

    def test_search_escalations_filter_resolved_before(self):
        """Test filtering escalations resolved before a date."""
        result_list = SearchEscalations.invoke(
            self.data,
            resolved_before="2025-09-02T00:00:00Z",
        )

        # Should only include escalations resolved before the date
        self.assertEqual(len(result_list), 1)

    def test_search_escalations_multiple_filters(self):
        """Test searching with multiple filters."""
        result_list = SearchEscalations.invoke(
            self.data,
            escalation_type="product_specialist",
            destination="product_management",
        )

        # Should match escalations that satisfy all filters
        self.assertEqual(len(result_list), 2)
        for escalation in result_list:
            self.assertEqual(escalation["escalationType"], "product_specialist")
            self.assertEqual(escalation["destination"], "product_management")

    def test_search_escalations_with_limit(self):
        """Test limiting the number of results."""
        result_list = SearchEscalations.invoke(
            self.data,
            limit=2,
        )

        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_escalations_limit_max_200(self):
        """Test that limit is capped at 200."""
        result_list = SearchEscalations.invoke(
            self.data,
            limit=500,  # Request more than max
        )

        # Should return at most 200 results
        self.assertLessEqual(len(result_list), 200)

    def test_search_escalations_default_limit(self):
        """Test that default limit is 50."""
        result_list = SearchEscalations.invoke(self.data)

        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_escalations_sorted_by_created_at(self):
        """Test that results are sorted by createdAt DESC, then id ASC."""
        result_list = SearchEscalations.invoke(self.data)

        if len(result_list) >= 2:
            # Check that escalations are sorted by createdAt descending
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

    def test_search_escalations_no_results(self):
        """Test search with filters that match no escalations."""
        result_list = SearchEscalations.invoke(
            self.data,
            escalation_id="nonexistent",
        )

        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchEscalations.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "searchEscalations")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("escalation_id", info["function"]["parameters"]["properties"])
        self.assertIn("ticket_id", info["function"]["parameters"]["properties"])
        self.assertIn("escalation_type", info["function"]["parameters"]["properties"])
        self.assertIn("destination", info["function"]["parameters"]["properties"])
        self.assertIn("notes_text", info["function"]["parameters"]["properties"])
        self.assertIn("created_after", info["function"]["parameters"]["properties"])
        self.assertIn("created_before", info["function"]["parameters"]["properties"])
        self.assertIn("resolved_after", info["function"]["parameters"]["properties"])
        self.assertIn("resolved_before", info["function"]["parameters"]["properties"])
        self.assertIn("limit", info["function"]["parameters"]["properties"])
        # All parameters are optional
        self.assertEqual(info["function"]["parameters"].get("required", []), [])


if __name__ == "__main__":
    unittest.main()
