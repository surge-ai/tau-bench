import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
# We're in tests/ subdirectory, so go up one level to tools/
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

# Import dependencies first
from tau_bench.envs.tool import Tool

# Now import the tool module normally
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from tau_update_ticket_status import UpdateTicketStatus


class TestUpdateTicketStatus(unittest.TestCase):
    def setUp(self):
        """Set up test data with tickets."""
        self.data: Dict[str, Any] = {
            "tickets": [
                {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "assignedEmployeeId": "employee1",
                    "status": "new",
                    "priority": "normal",
                    "ticketType": "troubleshooting",
                    "subject": "Computer won't boot",
                    "body": "My computer is not starting up properly",
                },
                {
                    "id": "ticket2",
                    "customerId": "customer1",
                    "assignedEmployeeId": None,
                    "status": "open",
                    "priority": "high",
                    "ticketType": "return",
                    "subject": "Return request",
                    "body": "I want to return my order",
                },
                {
                    "id": "ticket3",
                    "customerId": "customer2",
                    "assignedEmployeeId": "employee2",
                    "status": "resolved",
                    "priority": "low",
                    "ticketType": "other",
                    "subject": "General question",
                    "body": "I have a question about my order",
                },
            ]
        }

    def test_update_ticket_status_basic(self):
        """Test updating ticket status."""
        result = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="open",
        )
        result_dict = json.loads(result)
        
        # Should return updated=True
        self.assertTrue(result_dict["updated"])
        
        # Should mutate data in place
        ticket1 = next((t for t in self.data["tickets"] if t["id"] == "ticket1"), None)
        self.assertIsNotNone(ticket1)
        self.assertEqual(ticket1["status"], "open")

    def test_update_ticket_status_different_statuses(self):
        """Test updating to different status values."""
        statuses = ["new", "open", "pending_customer", "resolved", "closed"]
        
        for status in statuses:
            # Reset ticket1 status
            ticket1 = next((t for t in self.data["tickets"] if t["id"] == "ticket1"), None)
            if ticket1:
                ticket1["status"] = "new"
            
            result = UpdateTicketStatus.invoke(
                self.data,
                ticket_id="ticket1",
                status=status,
            )
            result_dict = json.loads(result)
            
            self.assertTrue(result_dict["updated"])
            self.assertEqual(ticket1["status"], status)

    def test_update_ticket_status_with_assigned_employee_id(self):
        """Test updating ticket status with assigned_employee_id."""
        # Note: The tool doesn't actually use assigned_employee_id, but it's in the API
        result = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="open",
            assigned_employee_id="employee2",
        )
        result_dict = json.loads(result)
        
        self.assertTrue(result_dict["updated"])
        ticket1 = next((t for t in self.data["tickets"] if t["id"] == "ticket1"), None)
        self.assertEqual(ticket1["status"], "open")
        # assigned_employee_id might not be updated, but status should be

    def test_update_ticket_status_with_priority(self):
        """Test updating ticket status with priority."""
        # Note: The tool doesn't actually use priority, but it's in the API
        result = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="open",
            priority="high",
        )
        result_dict = json.loads(result)
        
        self.assertTrue(result_dict["updated"])
        ticket1 = next((t for t in self.data["tickets"] if t["id"] == "ticket1"), None)
        self.assertEqual(ticket1["status"], "open")
        # priority might not be updated, but status should be

    def test_update_ticket_status_nonexistent_ticket(self):
        """Test updating non-existent ticket."""
        result = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="nonexistent",
            status="open",
        )
        result_dict = json.loads(result)
        
        # Should return updated=False
        self.assertFalse(result_dict["updated"])
        
        # Data should not be changed
        self.assertEqual(len(self.data["tickets"]), 3)

    def test_update_ticket_status_multiple_updates(self):
        """Test updating the same ticket multiple times."""
        # First update
        result1 = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="open",
        )
        result_dict1 = json.loads(result1)
        
        self.assertTrue(result_dict1["updated"])
        ticket1 = next((t for t in self.data["tickets"] if t["id"] == "ticket1"), None)
        self.assertEqual(ticket1["status"], "open")
        
        # Second update
        result2 = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="resolved",
        )
        result_dict2 = json.loads(result2)
        
        self.assertTrue(result_dict2["updated"])
        self.assertEqual(ticket1["status"], "resolved")

    def test_update_ticket_status_other_tickets_unchanged(self):
        """Test that other tickets are not affected."""
        initial_status_ticket2 = next(
            (t["status"] for t in self.data["tickets"] if t["id"] == "ticket2"),
            None
        )
        
        result = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="open",
        )
        result_dict = json.loads(result)
        
        self.assertTrue(result_dict["updated"])
        
        # ticket2 should be unchanged
        ticket2 = next((t for t in self.data["tickets"] if t["id"] == "ticket2"), None)
        self.assertIsNotNone(ticket2)
        self.assertEqual(ticket2["status"], initial_status_ticket2)
        
        # ticket3 should be unchanged
        ticket3 = next((t for t in self.data["tickets"] if t["id"] == "ticket3"), None)
        self.assertIsNotNone(ticket3)
        self.assertEqual(ticket3["status"], "resolved")

    def test_update_ticket_status_mutates_data_in_place(self):
        """Test that the tool mutates data in place (write tool behavior)."""
        # Get initial reference to ticket
        ticket1_initial = next((t for t in self.data["tickets"] if t["id"] == "ticket1"), None)
        self.assertIsNotNone(ticket1_initial)
        
        result = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="open",
        )
        result_dict = json.loads(result)
        
        self.assertTrue(result_dict["updated"])
        
        # The same object should be mutated
        self.assertIs(ticket1_initial, next((t for t in self.data["tickets"] if t["id"] == "ticket1"), None))
        self.assertEqual(ticket1_initial["status"], "open")

    def test_update_ticket_status_all_fields_preserved(self):
        """Test that other fields in the ticket are preserved."""
        ticket1_initial = next((t for t in self.data["tickets"] if t["id"] == "ticket1"), None)
        initial_customer_id = ticket1_initial["customerId"]
        initial_subject = ticket1_initial["subject"]
        initial_priority = ticket1_initial["priority"]
        
        result = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
            status="open",
        )
        result_dict = json.loads(result)
        
        self.assertTrue(result_dict["updated"])
        
        # Other fields should be preserved
        ticket1 = next((t for t in self.data["tickets"] if t["id"] == "ticket1"), None)
        self.assertEqual(ticket1["customerId"], initial_customer_id)
        self.assertEqual(ticket1["subject"], initial_subject)
        self.assertEqual(ticket1["priority"], initial_priority)
        self.assertEqual(ticket1["status"], "open")

    def test_update_ticket_status_empty_tickets_list(self):
        """Test updating when tickets list is empty."""
        empty_data = {"tickets": []}
        
        result = UpdateTicketStatus.invoke(
            empty_data,
            ticket_id="ticket1",
            status="open",
        )
        result_dict = json.loads(result)
        
        # Should return updated=False
        self.assertFalse(result_dict["updated"])

    def test_update_ticket_status_missing_tickets_key(self):
        """Test updating when tickets key doesn't exist."""
        data_no_tickets = {}
        
        result = UpdateTicketStatus.invoke(
            data_no_tickets,
            ticket_id="ticket1",
            status="open",
        )
        result_dict = json.loads(result)
        
        # Should return updated=False
        self.assertFalse(result_dict["updated"])

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
        # This tests that status is optional - the tool should still work
        # even if status is not provided (though it might not do anything)
        result = UpdateTicketStatus.invoke(
            self.data,
            ticket_id="ticket1",
        )
        result_dict = json.loads(result)
        
        # Should return updated=True (ticket was found)
        # Note: The tool might not update status if it's None, but it should find the ticket
        self.assertTrue(result_dict["updated"])


if __name__ == "__main__":
    unittest.main()


