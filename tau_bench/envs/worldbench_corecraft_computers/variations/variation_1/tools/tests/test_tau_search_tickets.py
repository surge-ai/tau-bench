import json
import unittest
from typing import Dict, Any

from ..tau_search_tickets import SearchTickets


class TestSearchTickets(unittest.TestCase):
    def setUp(self):
        """Set up test data with support tickets."""
        self.data: Dict[str, Any] = {
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "assignedEmployeeId": "employee1",
                    "status": "open",
                    "priority": "high",
                    "ticketType": "troubleshooting",
                    "subject": "Computer won't boot",
                    "body": "My computer is not starting up properly",
                    "createdAt": "2025-09-01T00:00:00Z",
                    "updatedAt": "2025-09-01T01:00:00Z",
                },
                "ticket2": {
                    "id": "ticket2",
                    "customerId": "customer1",
                    "assignedEmployeeId": "employee2",
                    "status": "resolved",
                    "priority": "normal",
                    "ticketType": "return",
                    "subject": "Return request",
                    "body": "I want to return my order",
                    "createdAt": "2025-09-02T00:00:00Z",
                    "updatedAt": "2025-09-02T01:00:00Z",
                },
                "ticket3": {
                    "id": "ticket3",
                    "customerId": "customer2",
                    "assignedEmployeeId": None,
                    "status": "new",
                    "priority": "low",
                    "ticketType": "other",
                    "subject": "General question",
                    "body": "I have a question about my order",
                    "createdAt": "2025-09-03T00:00:00Z",
                    "updatedAt": "2025-09-03T01:00:00Z",
                },
            }
        }

    def test_search_tickets_no_filters(self):
        """Test searching tickets with no filters."""
        result = SearchTickets.invoke(self.data)
        result_list = json.loads(result)

        # Should return all tickets (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertEqual(len(result_list), 3)

        # Check structure of first ticket
        if result_list:
            ticket = result_list[0]
            self.assertIn("id", ticket)
            self.assertIn("customerId", ticket)
            self.assertIn("status", ticket)

    def test_search_tickets_by_id(self):
        """Test searching tickets by exact ID."""
        result = SearchTickets.invoke(
            self.data,
            ticket_id="ticket1",
        )
        result_list = json.loads(result)

        # Should return exactly one ticket
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["id"], "ticket1")

    def test_search_tickets_by_customer_id(self):
        """Test searching tickets by customer ID."""
        result = SearchTickets.invoke(
            self.data,
            customer_id="customer1",
        )
        result_list = json.loads(result)

        # Should return tickets for customer1
        self.assertEqual(len(result_list), 2)
        for ticket in result_list:
            self.assertEqual(ticket["customerId"], "customer1")

    def test_search_tickets_by_assigned_employee_id(self):
        """Test searching tickets by assigned employee ID."""
        result = SearchTickets.invoke(
            self.data,
            assigned_employee_id="employee1",
        )
        result_list = json.loads(result)

        # Should return tickets assigned to employee1
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["assignedEmployeeId"], "employee1")

    def test_search_tickets_by_status(self):
        """Test searching tickets by status."""
        result = SearchTickets.invoke(
            self.data,
            status="open",
        )
        result_list = json.loads(result)

        # Should return tickets with open status
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["status"], "open")

    def test_search_tickets_by_priority(self):
        """Test searching tickets by priority."""
        result = SearchTickets.invoke(
            self.data,
            priority="high",
        )
        result_list = json.loads(result)

        # Should return tickets with high priority
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["priority"], "high")

    def test_search_tickets_by_ticket_type(self):
        """Test searching tickets by ticket type."""
        result = SearchTickets.invoke(
            self.data,
            ticket_type="troubleshooting",
        )
        result_list = json.loads(result)

        # Should return tickets with troubleshooting type
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["ticketType"], "troubleshooting")

    def test_search_tickets_by_text(self):
        """Test searching tickets by text (searches subject and body)."""
        result = SearchTickets.invoke(
            self.data,
            text="boot",
        )
        result_list = json.loads(result)

        # Should find tickets with "boot" in subject or body
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["id"], "ticket1")

    def test_search_tickets_filter_created_after(self):
        """Test filtering tickets created after a date."""
        result = SearchTickets.invoke(
            self.data,
            created_after="2025-09-02T00:00:00Z",
        )
        result_list = json.loads(result)

        # Should only include tickets created on or after 2025-09-02
        self.assertEqual(len(result_list), 2)
        for ticket in result_list:
            self.assertGreaterEqual(ticket["createdAt"], "2025-09-02T00:00:00Z")

    def test_search_tickets_filter_created_before(self):
        """Test filtering tickets created before a date."""
        result = SearchTickets.invoke(
            self.data,
            created_before="2025-09-02T12:00:00Z",
        )
        result_list = json.loads(result)

        # Should only include tickets created before the date
        self.assertEqual(len(result_list), 2)

    def test_search_tickets_filter_resolved_after(self):
        """Test filtering tickets resolved after a date (uses updatedAt)."""
        result = SearchTickets.invoke(
            self.data,
            resolved_after="2025-09-02T00:00:00Z",
        )
        result_list = json.loads(result)

        # Should only include tickets updated on or after the date
        self.assertEqual(len(result_list), 2)

    def test_search_tickets_filter_resolved_before(self):
        """Test filtering tickets resolved before a date (uses updatedAt)."""
        result = SearchTickets.invoke(
            self.data,
            resolved_before="2025-09-02T12:00:00Z",
        )
        result_list = json.loads(result)

        # Should only include tickets updated before the date
        self.assertEqual(len(result_list), 2)

    def test_search_tickets_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchTickets.invoke(
            self.data,
            customer_id="customer1",
            status="open",
            priority="high",
        )
        result_list = json.loads(result)

        # Should match tickets that satisfy all filters
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["customerId"], "customer1")
        self.assertEqual(result_list[0]["status"], "open")
        self.assertEqual(result_list[0]["priority"], "high")

    def test_search_tickets_with_limit(self):
        """Test limiting the number of results."""
        result = SearchTickets.invoke(
            self.data,
            limit=2,
        )
        result_list = json.loads(result)

        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_tickets_limit_max_200(self):
        """Test that limit is capped at 200."""
        result = SearchTickets.invoke(
            self.data,
            limit=500,  # Request more than max
        )
        result_list = json.loads(result)

        # Should return at most 200 results
        self.assertLessEqual(len(result_list), 200)

    def test_search_tickets_default_limit(self):
        """Test that default limit is 50."""
        result = SearchTickets.invoke(self.data)
        result_list = json.loads(result)

        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_tickets_sorted_by_priority(self):
        """Test that results are sorted by priority (high -> normal -> low), then createdAt DESC."""
        result = SearchTickets.invoke(self.data)
        result_list = json.loads(result)

        if len(result_list) >= 2:
            # Check that tickets are sorted by priority first
            priority_order = {"high": 1, "normal": 2, "low": 3}
            for i in range(len(result_list) - 1):
                current_priority = result_list[i]["priority"]
                next_priority = result_list[i + 1]["priority"]
                current_priority_val = priority_order.get(current_priority, 4)
                next_priority_val = priority_order.get(next_priority, 4)

                # Priority should be in ascending order (high first)
                if current_priority_val == next_priority_val:
                    # If priorities are equal, check createdAt (descending)
                    current_created = result_list[i]["createdAt"]
                    next_created = result_list[i + 1]["createdAt"]
                    if current_created == next_created:
                        # If createdAt is equal, check IDs
                        current_id = result_list[i]["id"]
                        next_id = result_list[i + 1]["id"]
                        self.assertLessEqual(current_id, next_id)
                    else:
                        self.assertGreaterEqual(current_created, next_created)
                else:
                    self.assertLessEqual(current_priority_val, next_priority_val)

    def test_search_tickets_no_results(self):
        """Test search with filters that match no tickets."""
        result = SearchTickets.invoke(
            self.data,
            ticket_id="nonexistent",
        )
        result_list = json.loads(result)

        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchTickets.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "searchTickets")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("ticket_id", info["function"]["parameters"]["properties"])
        self.assertIn("customer_id", info["function"]["parameters"]["properties"])
        self.assertIn("assigned_employee_id", info["function"]["parameters"]["properties"])
        self.assertIn("status", info["function"]["parameters"]["properties"])
        self.assertIn("priority", info["function"]["parameters"]["properties"])
        self.assertIn("ticket_type", info["function"]["parameters"]["properties"])
        self.assertIn("text", info["function"]["parameters"]["properties"])
        self.assertIn("created_after", info["function"]["parameters"]["properties"])
        self.assertIn("created_before", info["function"]["parameters"]["properties"])
        self.assertIn("resolved_after", info["function"]["parameters"]["properties"])
        self.assertIn("resolved_before", info["function"]["parameters"]["properties"])
        self.assertIn("limit", info["function"]["parameters"]["properties"])
        # All parameters are optional
        self.assertEqual(info["function"]["parameters"].get("required", []), [])


if __name__ == "__main__":
    unittest.main()
