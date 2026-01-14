import unittest
from typing import Dict, Any

from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tools.tau_update_ticket_status import UpdateTicketStatus


class TestUpdateTicketStatus(unittest.TestCase):
    def setUp(self):
        """Set up test data with support tickets."""
        self.data: Dict[str, Any] = {
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "assignedEmployeeId": "employee1",
                    "status": "new",
                    "priority": "normal",
                    "ticketType": "troubleshooting",
                    "subject": "Computer won't boot",
                    "body": "My computer is not starting up properly",
                },
                "ticket2": {
                    "id": "ticket2",
                    "customerId": "customer1",
                    "assignedEmployeeId": None,
                    "status": "open",
                    "priority": "high",
                    "ticketType": "return",
                    "subject": "Return request",
                    "body": "I want to return my order",
                },
                "ticket3": {
                    "id": "ticket3",
                    "customerId": "customer2",
                    "assignedEmployeeId": "employee2",
                    "status": "resolved",
                    "priority": "low",
                    "ticketType": "other",
                    "subject": "General question",
                    "body": "I have a question about my order",
                },
            }
        }

    def test_update_ticket_status_basic(self):
        """Test updating ticket status."""
        result_dict = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="open",
        )

        # Should return the updated ticket
        self.assertEqual(result_dict["id"], "ticket1")
        self.assertEqual(result_dict["status"], "open")

        # Should mutate data in place
        self.assertEqual(self.data["support_ticket"]["ticket1"]["status"], "open")

    def test_update_ticket_status_different_statuses(self):
        """Test updating to different status values."""
        statuses = ["new", "open", "pending_customer", "resolved", "closed"]

        for status in statuses:
            # Reset ticket1 status
            self.data["support_ticket"]["ticket1"]["status"] = "new"

            result_dict = UpdateTicketStatus.invoke(
                self.data,
                ticket_id="ticket1",
                status=status,
            )

            self.assertEqual(result_dict["status"], status)
            self.assertEqual(self.data["support_ticket"]["ticket1"]["status"], status)

    def test_update_ticket_status_with_assigned_employee_id(self):
        """Test updating ticket with assigned_employee_id."""
        result_dict = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="open",
            assigned_employee_id="employee2",
        )

        self.assertEqual(result_dict["status"], "open")
        self.assertEqual(result_dict["assignedEmployeeId"], "employee2")
        self.assertEqual(self.data["support_ticket"]["ticket1"]["status"], "open")
        self.assertEqual(self.data["support_ticket"]["ticket1"]["assignedEmployeeId"], "employee2")

    def test_update_ticket_status_with_priority(self):
        """Test updating ticket with priority."""
        result_dict = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="open",
            priority="high",
        )

        self.assertEqual(result_dict["status"], "open")
        self.assertEqual(result_dict["priority"], "high")
        self.assertEqual(self.data["support_ticket"]["ticket1"]["status"], "open")
        self.assertEqual(self.data["support_ticket"]["ticket1"]["priority"], "high")

    def test_update_ticket_status_nonexistent_ticket(self):
        """Test updating non-existent ticket raises ValueError."""
        with self.assertRaises(ValueError) as context:
            UpdateTicketStatus.invoke(
                self.data,
                ticket_id="nonexistent",
                status="open",
            )

        self.assertIn("nonexistent", str(context.exception))
        self.assertIn("not found", str(context.exception))

        # Data should not be changed
        self.assertEqual(len(self.data["support_ticket"]), 3)

    def test_update_ticket_status_multiple_updates(self):
        """Test updating the same ticket multiple times."""
        # First update
        result_dict1 = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="open",
        )

        self.assertEqual(result_dict1["status"], "open")
        self.assertEqual(self.data["support_ticket"]["ticket1"]["status"], "open")

        # Second update
        result_dict2 = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="resolved",
        )

        self.assertEqual(result_dict2["status"], "resolved")
        self.assertEqual(self.data["support_ticket"]["ticket1"]["status"], "resolved")

    def test_update_ticket_status_other_tickets_unchanged(self):
        """Test that other tickets are not affected."""
        initial_status_ticket2 = self.data["support_ticket"]["ticket2"]["status"]

        result_dict = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="open",
        )

        self.assertEqual(result_dict["status"], "open")

        # ticket2 should be unchanged
        self.assertEqual(self.data["support_ticket"]["ticket2"]["status"], initial_status_ticket2)

        # ticket3 should be unchanged
        self.assertEqual(self.data["support_ticket"]["ticket3"]["status"], "resolved")

    def test_update_ticket_status_mutates_data_in_place(self):
        """Test that the tool mutates data in place (write tool behavior)."""
        # Get initial reference to ticket
        ticket1_initial = self.data["support_ticket"]["ticket1"]
        self.assertIsNotNone(ticket1_initial)

        result_dict = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="open",
        )

        self.assertEqual(result_dict["status"], "open")

        # The same object should be mutated
        self.assertIs(ticket1_initial, self.data["support_ticket"]["ticket1"])
        self.assertEqual(ticket1_initial["status"], "open")

    def test_update_ticket_status_all_fields_preserved(self):
        """Test that other fields in the ticket are preserved."""
        ticket1_initial = self.data["support_ticket"]["ticket1"]
        initial_customer_id = ticket1_initial["customerId"]
        initial_subject = ticket1_initial["subject"]
        initial_priority = ticket1_initial["priority"]

        result_dict = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="open",
        )

        self.assertEqual(result_dict["status"], "open")
        self.assertEqual(result_dict["customerId"], initial_customer_id)
        self.assertEqual(result_dict["subject"], initial_subject)

        # Other fields should be preserved in data
        self.assertEqual(self.data["support_ticket"]["ticket1"]["customerId"], initial_customer_id)
        self.assertEqual(self.data["support_ticket"]["ticket1"]["subject"], initial_subject)
        self.assertEqual(self.data["support_ticket"]["ticket1"]["priority"], initial_priority)
        self.assertEqual(self.data["support_ticket"]["ticket1"]["status"], "open")

    def test_update_ticket_status_empty_tickets(self):
        """Test updating when tickets dict is empty raises ValueError."""
        empty_data = {"support_ticket": {}}

        with self.assertRaises(ValueError) as context:
            UpdateTicketStatus.invoke(
                empty_data,
                ticket_id="ticket1",
                status="open",
            )

        self.assertIn("not found", str(context.exception))

    def test_update_ticket_status_missing_tickets_key(self):
        """Test updating when support_ticket key doesn't exist raises ValueError."""
        data_no_tickets = {}

        with self.assertRaises(ValueError) as context:
            UpdateTicketStatus.invoke(
                data_no_tickets,
                ticket_id="ticket1",
                status="open",
            )

        self.assertIn("table not found", str(context.exception).lower())

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = UpdateTicketStatus.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "updateTicketStatus")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("ticket_id", info["function"]["parameters"]["properties"])
        self.assertIn("status", info["function"]["parameters"]["properties"])
        self.assertIn("assigned_employee_id", info["function"]["parameters"]["properties"])
        self.assertIn("priority", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("ticket_id", required)
        # status is optional according to the API

    def test_update_ticket_status_status_optional(self):
        """Test that status can be omitted (only ticket_id is required)."""
        # Update only priority, not status
        result_dict = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            priority="high",
        )

        # Should return the ticket with updated priority
        self.assertEqual(result_dict["id"], "ticket1")
        self.assertEqual(result_dict["priority"], "high")
        # Status should be unchanged
        self.assertEqual(result_dict["status"], "new")


if __name__ == "__main__":
    unittest.main()
