import json
import unittest
from typing import Dict, Any

from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tools.tau_get_customer_ticket_history import GetCustomerTicketHistory


class TestGetCustomerTicketHistory(unittest.TestCase):
    def setUp(self):
        """Set up test data with support tickets, escalations, and resolutions."""
        self.data: Dict[str, Any] = {
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "ticketType": "troubleshooting",
                    "status": "open",
                    "priority": "high",
                    "subject": "Test ticket 1",
                    "createdAt": "2025-09-01T00:00:00Z",
                    "updatedAt": "2025-09-01T01:00:00Z",
                },
                "ticket2": {
                    "id": "ticket2",
                    "customerId": "customer1",
                    "ticketType": "other",
                    "status": "resolved",
                    "priority": "medium",
                    "subject": "Test ticket 2",
                    "createdAt": "2025-09-02T00:00:00Z",
                    "updatedAt": "2025-09-02T01:00:00Z",
                },
                "ticket3": {
                    "id": "ticket3",
                    "customerId": "customer1",
                    "ticketType": "troubleshooting",
                    "status": "closed",
                    "priority": "low",
                    "subject": "Test ticket 3",
                    "createdAt": "2025-09-03T00:00:00Z",
                    "updatedAt": "2025-09-03T01:00:00Z",
                },
                "ticket4": {
                    "id": "ticket4",
                    "customerId": "customer2",
                    "ticketType": "other",
                    "status": "open",
                    "priority": "normal",
                    "subject": "Test ticket 4",
                    "createdAt": "2025-09-04T00:00:00Z",
                    "updatedAt": "2025-09-04T01:00:00Z",
                },
            },
            "escalation": {
                "esc1": {
                    "id": "esc1",
                    "ticketId": "ticket1",
                    "escalationType": "technical",
                    "destination": "engineering",
                    "createdAt": "2025-09-01T02:00:00Z",
                }
            },
            "resolution": {
                "res1": {
                    "id": "res1",
                    "ticketId": "ticket2",
                    "outcome": "refund_approved",
                    "details": "Refund was approved for customer",
                    "createdAt": "2025-09-02T02:00:00Z",
                },
                "res2": {
                    "id": "res2",
                    "ticketId": "ticket3",
                    "outcome": "replacement_provided",
                    "details": "Replacement product provided",
                    "createdAt": "2025-09-03T02:00:00Z",
                }
            }
        }

    def test_get_ticket_history_basic(self):
        """Test getting ticket history for a customer."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        result_dict = json.loads(result)

        # Should return tickets for customer1
        self.assertIn("tickets", result_dict)
        tickets = result_dict["tickets"]
        self.assertGreater(len(tickets), 0)

        # All tickets should be for customer1
        for ticket in tickets:
            self.assertEqual(ticket["customerId"], "customer1")
            self.assertIn("id", ticket)
            self.assertIn("status", ticket)

    def test_get_ticket_history_excludes_other_customers(self):
        """Test that tickets from other customers are excluded."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        result_dict = json.loads(result)

        tickets = result_dict["tickets"]
        ticket_ids = [t["id"] for t in tickets]

        # Should not include ticket4 (customer2)
        self.assertNotIn("ticket4", ticket_ids)
        # Should include customer1 tickets
        self.assertIn("ticket1", ticket_ids)
        self.assertIn("ticket2", ticket_ids)
        self.assertIn("ticket3", ticket_ids)

    def test_get_ticket_history_include_resolved_default(self):
        """Test that resolved/closed tickets are included by default."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        result_dict = json.loads(result)

        tickets = result_dict["tickets"]
        ticket_ids = [t["id"] for t in tickets]

        # Should include resolved and closed tickets
        self.assertIn("ticket2", ticket_ids)  # resolved
        self.assertIn("ticket3", ticket_ids)  # closed

    def test_get_ticket_history_exclude_resolved(self):
        """Test excluding resolved/closed tickets."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
            include_resolved="false",
        )
        result_dict = json.loads(result)

        tickets = result_dict["tickets"]
        ticket_ids = [t["id"] for t in tickets]

        # Should only include open tickets
        self.assertIn("ticket1", ticket_ids)  # open
        self.assertNotIn("ticket2", ticket_ids)  # resolved
        self.assertNotIn("ticket3", ticket_ids)  # closed

    def test_get_ticket_history_filter_created_after(self):
        """Test filtering tickets created after a date."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
            tkt_created_after="2025-09-02T00:00:00Z",
        )
        result_dict = json.loads(result)

        tickets = result_dict["tickets"]

        # Should only include tickets created on or after 2025-09-02
        for ticket in tickets:
            self.assertGreaterEqual(ticket["createdAt"], "2025-09-02T00:00:00Z")

    def test_get_ticket_history_filter_created_before(self):
        """Test filtering tickets created before a date."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
            tkt_created_before="2025-09-02T12:00:00Z",
        )
        result_dict = json.loads(result)

        tickets = result_dict["tickets"]

        # Should have 2 tickets (ticket1 and ticket2)
        self.assertLessEqual(len(tickets), 2)

    def test_get_ticket_history_includes_escalations(self):
        """Test that escalations are included in the response."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        result_dict = json.loads(result)

        # Should have escalations field
        self.assertIn("escalations", result_dict)
        escalations = result_dict["escalations"]

        # Should include escalation for ticket1
        self.assertGreater(len(escalations), 0)
        ticket1_escalations = [e for e in escalations if e.get("ticketId") == "ticket1"]
        self.assertGreater(len(ticket1_escalations), 0)

    def test_get_ticket_history_includes_resolutions(self):
        """Test that resolutions are included in the response."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        result_dict = json.loads(result)

        # Should have resolutions field
        self.assertIn("resolutions", result_dict)
        resolutions = result_dict["resolutions"]

        # Should include resolutions for ticket2 and ticket3
        self.assertGreater(len(resolutions), 0)
        resolution_ticket_ids = [r.get("ticketId") for r in resolutions]
        self.assertIn("ticket2", resolution_ticket_ids)
        self.assertIn("ticket3", resolution_ticket_ids)

    def test_get_ticket_history_empty_result(self):
        """Test getting history for customer with no tickets."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="nonexistent_customer",
        )
        result_dict = json.loads(result)

        # Should return empty lists
        self.assertIn("tickets", result_dict)
        self.assertEqual(len(result_dict["tickets"]), 0)
        self.assertIn("escalations", result_dict)
        self.assertEqual(len(result_dict["escalations"]), 0)
        self.assertIn("resolutions", result_dict)
        self.assertEqual(len(result_dict["resolutions"]), 0)

    def test_get_ticket_history_tickets_sorted(self):
        """Test that tickets are sorted by createdAt DESC, then id ASC."""
        result = GetCustomerTicketHistory.invoke(
            self.data,
            customer_id="customer1",
        )
        result_dict = json.loads(result)

        tickets = result_dict["tickets"]

        # Should be sorted: newest first (ticket3, ticket2, ticket1)
        if len(tickets) >= 2:
            # Check that tickets are in descending order by createdAt
            for i in range(len(tickets) - 1):
                current_created = tickets[i]["createdAt"]
                next_created = tickets[i + 1]["createdAt"]
                self.assertGreaterEqual(current_created, next_created)

    def test_get_ticket_history_missing_customer_id(self):
        """Test that missing customer_id raises an error."""
        with self.assertRaises((TypeError, ValueError)):
            GetCustomerTicketHistory.invoke(self.data)

    def test_get_ticket_history_empty_customer_id(self):
        """Test that empty customer_id raises an error."""
        with self.assertRaises(ValueError):
            GetCustomerTicketHistory.invoke(
                self.data,
                customer_id="",
            )

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = GetCustomerTicketHistory.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "getCustomerTicketHistory")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("customer_id", info["function"]["parameters"]["properties"])
        self.assertIn("include_resolved", info["function"]["parameters"]["properties"])
        self.assertIn("tkt_created_after", info["function"]["parameters"]["properties"])
        self.assertIn("tkt_created_before", info["function"]["parameters"]["properties"])
        self.assertIn("tkt_updated_after", info["function"]["parameters"]["properties"])
        self.assertIn("tkt_updated_before", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("customer_id", info["function"]["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()
