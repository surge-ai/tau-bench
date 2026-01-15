import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_process_customer_issue import ProcessCustomerIssue


class TestProcessCustomerIssue(unittest.TestCase):
    def setUp(self):
        """Set up test data with customers and orders."""
        self.data: Dict[str, Any] = {
            "__now": "2025-01-15T12:00:00Z",
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
                    "loyaltyTier": "platinum",
                },
                "customer3": {
                    "id": "customer3",
                    "name": "Bob Wilson",
                    "email": "bob@example.com",
                    "loyaltyTier": "none",
                },
            },
            "order": {
                "order1": {
                    "id": "order1",
                    "customerId": "customer1",
                    "status": "paid",
                },
            },
        }

    def test_process_issue_creates_ticket(self):
        """Test that processing an issue creates a support ticket."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="defective_item",
            description="Product arrived broken",
        )

        self.assertTrue(result["success"])
        self.assertIn("ticket", result)

        ticket = result["ticket"]
        self.assertIn("id", ticket)
        self.assertTrue(ticket["id"].startswith("ticket_"))
        self.assertEqual(ticket["type"], "support_ticket")
        self.assertEqual(ticket["customerId"], "customer1")

        # BUG: Line 70 sets "description" but SupportTicket has "body" field
        self.assertIn("description", ticket)  # Bug: wrong field name
        self.assertEqual(ticket["description"], "Product arrived broken")

        # BUG: Line 73 sets "category" but SupportTicket has "ticketType" field
        self.assertIn("category", ticket)  # Bug: wrong field name
        self.assertEqual(ticket["category"], "defective_item")

    def test_process_issue_priority_high_for_damaged_product(self):
        """Test that damaged_product gets high priority."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="damaged_product",
            description="Package damaged",
        )

        self.assertEqual(result["priority"], "high")
        self.assertEqual(result["ticket"]["priority"], "high")

    def test_process_issue_priority_high_for_defective_item(self):
        """Test that defective_item gets high priority."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="defective_item",
            description="Item doesn't work",
        )

        self.assertEqual(result["priority"], "high")

    def test_process_issue_priority_high_for_missing_items(self):
        """Test that missing_items gets high priority."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="missing_items",
            description="Items missing from package",
        )

        self.assertEqual(result["priority"], "high")

    def test_process_issue_priority_medium_for_wrong_item(self):
        """Test that wrong_item gets medium priority."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="wrong_item",
            description="Received wrong item",
        )

        self.assertEqual(result["priority"], "medium")

    def test_process_issue_priority_low_for_general_inquiry(self):
        """Test that general_inquiry gets low priority."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="general_inquiry",
            description="Question about product",
        )

        self.assertEqual(result["priority"], "low")

    def test_process_issue_priority_boost_for_gold_customer(self):
        """Test that gold customers get boosted from medium to high."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",  # gold tier
            issue_type="shipping_delay",  # medium priority
            description="Shipping is delayed",
        )

        # Should be boosted from medium to high
        self.assertEqual(result["priority"], "high")

    def test_process_issue_priority_boost_for_platinum_customer(self):
        """Test that platinum customers get boosted from medium to high."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer2",  # platinum tier
            issue_type="billing_question",  # medium priority
            description="Question about billing",
        )

        # Should be boosted from medium to high
        self.assertEqual(result["priority"], "high")

    def test_process_issue_no_boost_for_regular_customer(self):
        """Test that regular customers don't get priority boost."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer3",  # none tier
            issue_type="shipping_delay",  # medium priority
            description="Shipping is delayed",
        )

        # Should stay medium
        self.assertEqual(result["priority"], "medium")

    def test_process_issue_no_boost_for_already_high_priority(self):
        """Test that high priority doesn't get boosted."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer2",  # platinum tier
            issue_type="defective_item",  # already high
            description="Item defective",
        )

        # Should stay high
        self.assertEqual(result["priority"], "high")

    def test_process_issue_with_order_id(self):
        """Test processing issue with order ID."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="defective_item",
            description="Item defective",
            order_id="order1",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["ticket"]["orderId"], "order1")

    def test_process_issue_without_order_id(self):
        """Test processing issue without order ID."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="general_inquiry",
            description="General question",
        )

        self.assertTrue(result["success"])
        self.assertIsNone(result["ticket"]["orderId"])

    def test_process_issue_auto_escalate_disabled(self):
        """Test that auto_escalate defaults to False."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="general_inquiry",
            description="Question",
        )

        self.assertFalse(result["auto_escalated"])
        self.assertIsNone(result["escalation"])

    def test_process_issue_auto_escalate_enabled(self):
        """Test explicit auto_escalate=True."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="general_inquiry",
            description="Question",
            auto_escalate=True,
        )

        self.assertTrue(result["auto_escalated"])
        self.assertIsNotNone(result["escalation"])

        # Verify escalation structure
        escalation = result["escalation"]
        self.assertIn("id", escalation)
        self.assertTrue(escalation["id"].startswith("esc_"))
        self.assertEqual(escalation["type"], "escalation")
        self.assertEqual(escalation["ticketId"], result["ticket"]["id"])

        # BUG: Line 105 sets status="pending", but Escalation model has no status field
        self.assertIn("status", escalation)  # Bug: non-schema field

    def test_process_issue_auto_escalate_for_damaged_product(self):
        """Test automatic escalation for damaged_product with high priority."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="damaged_product",
            description="Product damaged",
        )

        # Should auto-escalate (high priority + damaged_product)
        self.assertTrue(result["auto_escalated"])
        self.assertIsNotNone(result["escalation"])
        self.assertEqual(result["escalation"]["escalationType"], "technical")

    def test_process_issue_auto_escalate_for_defective_item(self):
        """Test automatic escalation for defective_item with high priority."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="defective_item",
            description="Item defective",
        )

        # Should auto-escalate (high priority + defective_item)
        self.assertTrue(result["auto_escalated"])
        self.assertEqual(result["escalation"]["escalationType"], "technical")

    def test_process_issue_no_auto_escalate_for_other_high_priority(self):
        """Test that other high priority issues don't auto-escalate."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="missing_items",  # high priority but not auto-escalate
            description="Items missing",
        )

        # Should NOT auto-escalate
        self.assertFalse(result["auto_escalated"])
        self.assertIsNone(result["escalation"])

    def test_process_issue_escalation_destination(self):
        """Test that escalation goes to correct destination."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="defective_item",
            description="Item defective",
        )

        self.assertEqual(result["escalation"]["destination"], "product_specialist_team")

    def test_process_issue_escalation_notes(self):
        """Test that escalation has notes."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="damaged_product",
            description="Product damaged",
        )

        self.assertIn("notes", result["escalation"])
        self.assertIn("damaged_product", result["escalation"]["notes"])

    def test_process_issue_ticket_subject(self):
        """Test ticket subject generation."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="defective_item",
            description="Item doesn't work",
        )

        subject = result["ticket"]["subject"]
        self.assertIn("Defective Item", subject)
        self.assertIn("John Doe", subject)

    def test_process_issue_ticket_status(self):
        """Test that ticket starts with open status."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="general_inquiry",
            description="Question",
        )

        self.assertEqual(result["ticket"]["status"], "open")

    def test_process_issue_ticket_timestamps(self):
        """Test that ticket has correct timestamps."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="general_inquiry",
            description="Question",
        )

        ticket = result["ticket"]
        self.assertEqual(ticket["createdAt"], "2025-01-15T12:00:00Z")
        self.assertEqual(ticket["updatedAt"], "2025-01-15T12:00:00Z")

        # BUG: Line 76 initializes resolvedAt=None, but SupportTicket has no resolvedAt field
        self.assertIn("resolvedAt", ticket)  # Bug: non-schema field
        self.assertIsNone(ticket["resolvedAt"])

    def test_process_issue_nonexistent_customer(self):
        """Test with non-existent customer."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="nonexistent",
            issue_type="general_inquiry",
            description="Question",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_process_issue_nonexistent_order(self):
        """Test with non-existent order."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="general_inquiry",
            description="Question",
            order_id="nonexistent",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_process_issue_creates_ticket_in_data(self):
        """Test that ticket is added to data."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="general_inquiry",
            description="Question",
        )

        ticket_id = result["ticket"]["id"]
        self.assertIn("support_ticket", self.data)
        self.assertIn(ticket_id, self.data["support_ticket"])

    def test_process_issue_creates_escalation_in_data(self):
        """Test that escalation is added to data when auto-escalated."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="defective_item",
            description="Item defective",
        )

        escalation_id = result["escalation"]["id"]
        self.assertIn("escalation", self.data)
        self.assertIn(escalation_id, self.data["escalation"])

    def test_process_issue_message_without_escalation(self):
        """Test message format without escalation."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="general_inquiry",
            description="Question",
        )

        message = result["message"]
        self.assertIn("Ticket", message)
        self.assertIn("created", message)
        self.assertIn("low priority", message)
        self.assertNotIn("escalated", message)

    def test_process_issue_message_with_escalation(self):
        """Test message format with escalation."""
        result = ProcessCustomerIssue.invoke(
            self.data,
            customer_id="customer1",
            issue_type="defective_item",
            description="Item defective",
        )

        message = result["message"]
        self.assertIn("escalated", message)
        self.assertIn("product_specialist_team", message)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = ProcessCustomerIssue.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "process_customer_issue")
        self.assertIn("description", info["function"])
        self.assertIn("CRITICAL", info["function"]["description"])
        self.assertIn("auto_escalate", info["function"]["description"])
        self.assertIn("parameters", info["function"])
        self.assertIn("customer_id", info["function"]["parameters"]["properties"])
        self.assertIn("issue_type", info["function"]["parameters"]["properties"])
        self.assertIn("description", info["function"]["parameters"]["properties"])
        self.assertIn("order_id", info["function"]["parameters"]["properties"])
        self.assertIn("auto_escalate", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("customer_id", required)
        self.assertIn("issue_type", required)
        self.assertIn("description", required)


if __name__ == "__main__":
    unittest.main()
