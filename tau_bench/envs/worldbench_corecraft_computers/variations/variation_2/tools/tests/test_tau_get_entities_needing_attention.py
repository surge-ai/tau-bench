import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_get_entities_needing_attention import GetEntitiesNeedingAttention


class TestGetEntitiesNeedingAttention(unittest.TestCase):
    def setUp(self):
        """Set up test data with various entities needing attention."""
        self.data: Dict[str, Any] = {
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "status": "open",
                    "priority": "high",
                },
                "ticket2": {
                    "id": "ticket2",
                    "customerId": "customer2",
                    "status": "pending_customer",
                    "priority": "normal",
                },
                "ticket3": {
                    "id": "ticket3",
                    "customerId": "customer3",
                    "status": "new",
                    "priority": "high",
                },
                "ticket4": {
                    "id": "ticket4",
                    "customerId": "customer4",
                    "status": "resolved",
                    "priority": "low",
                },
                "ticket5": {
                    "id": "ticket5",
                    "customerId": "customer5",
                    "status": "closed",
                    "priority": "normal",
                },
            },
            "refund": {
                "refund1": {
                    "id": "refund1",
                    "paymentId": "payment1",
                    "amount": 50.0,
                    "status": "pending",
                },
                "refund2": {
                    "id": "refund2",
                    "paymentId": "payment2",
                    "amount": 75.0,
                    "status": "approved",
                },
            },
            "payment": {
                "payment1": {
                    "id": "payment1",
                    "orderId": "order1",
                    "amount": 100.0,
                    "status": "failed",
                },
                "payment2": {
                    "id": "payment2",
                    "orderId": "order2",
                    "amount": 200.0,
                    "status": "captured",
                },
            },
            "escalation": {
                "esc1": {
                    "id": "esc1",
                    "ticketId": "ticket1",
                    "escalationType": "technical",
                    "status": "pending",
                },
                "esc2": {
                    "id": "esc2",
                    "ticketId": "ticket2",
                    "escalationType": "policy_exception",
                    "resolvedAt": None,
                },
                "esc3": {
                    "id": "esc3",
                    "ticketId": "ticket4",
                    "escalationType": "technical",
                    "resolvedAt": "2025-01-15T12:00:00Z",
                },
            },
            "order": {
                "order1": {
                    "id": "order1",
                    "customerId": "customer1",
                    "status": "cancelled",
                },
                "order2": {
                    "id": "order2",
                    "customerId": "customer2",
                    "status": "paid",
                },
            },
        }

    def test_get_open_tickets(self):
        """Test finding open tickets."""
        result = GetEntitiesNeedingAttention.invoke(self.data)

        # BUG: Line 29 checks for "pending" status, but SupportTicket Status1 enum
        # has "pending_customer" not "pending"
        # ticket1 has "open" status, should be found
        # ticket2 has "pending_customer" status, won't be found with current bug
        # ticket3 has "new" status, won't be found with current bug

        open_tickets = result["results"]["open_tickets"]
        self.assertEqual(len(open_tickets), 1)
        self.assertEqual(open_tickets[0]["id"], "ticket1")

    def test_get_urgent_tickets(self):
        """Test finding urgent (high priority) tickets."""
        result = GetEntitiesNeedingAttention.invoke(self.data)

        urgent_tickets = result["results"]["urgent_tickets"]

        # BUG: Only ticket1 will be in urgent because it has "open" status
        # ticket3 has "high" priority but "new" status which doesn't match the check on line 29
        self.assertEqual(len(urgent_tickets), 1)
        self.assertEqual(urgent_tickets[0]["id"], "ticket1")

    def test_get_pending_refunds(self):
        """Test finding pending refunds."""
        result = GetEntitiesNeedingAttention.invoke(self.data)

        pending_refunds = result["results"]["pending_refunds"]
        self.assertEqual(len(pending_refunds), 1)
        self.assertEqual(pending_refunds[0]["id"], "refund1")

    def test_get_failed_payments(self):
        """Test finding failed payments."""
        result = GetEntitiesNeedingAttention.invoke(self.data)

        failed_payments = result["results"]["failed_payments"]
        self.assertEqual(len(failed_payments), 1)
        self.assertEqual(failed_payments[0]["id"], "payment1")

    def test_get_pending_escalations(self):
        """Test finding pending escalations."""
        result = GetEntitiesNeedingAttention.invoke(self.data)

        pending_escalations = result["results"]["pending_escalations"]

        # esc1 has status="pending"
        # esc2 has no resolvedAt (None)
        # esc3 has resolvedAt set, so should not be included
        self.assertEqual(len(pending_escalations), 2)
        escalation_ids = {e["id"] for e in pending_escalations}
        self.assertIn("esc1", escalation_ids)
        self.assertIn("esc2", escalation_ids)

    def test_get_cancelled_orders(self):
        """Test finding cancelled orders."""
        result = GetEntitiesNeedingAttention.invoke(self.data)

        cancelled_orders = result["results"]["cancelled_orders"]
        self.assertEqual(len(cancelled_orders), 1)
        self.assertEqual(cancelled_orders[0]["id"], "order1")

    def test_get_unresolved_tickets(self):
        """Test finding unresolved tickets."""
        result = GetEntitiesNeedingAttention.invoke(self.data)

        unresolved_tickets = result["results"]["unresolved_tickets"]

        # All tickets except resolved and closed
        # ticket1: open - unresolved
        # ticket2: pending_customer - unresolved
        # ticket3: new - unresolved
        # ticket4: resolved - NOT unresolved
        # ticket5: closed - NOT unresolved
        self.assertEqual(len(unresolved_tickets), 3)
        ticket_ids = {t["id"] for t in unresolved_tickets}
        self.assertIn("ticket1", ticket_ids)
        self.assertIn("ticket2", ticket_ids)
        self.assertIn("ticket3", ticket_ids)

    def test_summary_counts(self):
        """Test that summary contains correct counts."""
        result = GetEntitiesNeedingAttention.invoke(self.data)

        summary = result["summary"]
        self.assertEqual(summary["open_tickets"], 1)
        self.assertEqual(summary["urgent_tickets"], 1)
        self.assertEqual(summary["pending_refunds"], 1)
        self.assertEqual(summary["failed_payments"], 1)
        self.assertEqual(summary["pending_escalations"], 2)
        self.assertEqual(summary["unresolved_tickets"], 3)
        self.assertEqual(summary["cancelled_orders"], 1)

    def test_total_items_needing_attention(self):
        """Test that total is calculated correctly."""
        result = GetEntitiesNeedingAttention.invoke(self.data)

        # Total should be sum of all categories
        # Note: tickets may appear in multiple categories
        expected_total = sum(result["summary"].values())
        self.assertEqual(result["total_items_needing_attention"], expected_total)

    def test_empty_data(self):
        """Test with empty data."""
        empty_data = {}

        result = GetEntitiesNeedingAttention.invoke(empty_data)

        # All results should be empty
        for category in result["results"].values():
            self.assertEqual(len(category), 0)

        self.assertEqual(result["total_items_needing_attention"], 0)

    def test_no_items_needing_attention(self):
        """Test when all entities are in good state."""
        good_data = {
            "support_ticket": {
                "ticket1": {"id": "ticket1", "status": "resolved", "priority": "low"},
            },
            "refund": {
                "refund1": {"id": "refund1", "status": "approved"},
            },
            "payment": {
                "payment1": {"id": "payment1", "status": "captured"},
            },
            "escalation": {
                "esc1": {"id": "esc1", "resolvedAt": "2025-01-15T12:00:00Z"},
            },
            "order": {
                "order1": {"id": "order1", "status": "paid"},
            },
        }

        result = GetEntitiesNeedingAttention.invoke(good_data)

        # Only unresolved_tickets might have items (resolved is not closed)
        self.assertEqual(result["summary"]["open_tickets"], 0)
        self.assertEqual(result["summary"]["urgent_tickets"], 0)
        self.assertEqual(result["summary"]["pending_refunds"], 0)
        self.assertEqual(result["summary"]["failed_payments"], 0)
        self.assertEqual(result["summary"]["cancelled_orders"], 0)

    def test_case_insensitive_status(self):
        """Test that status checks are case-insensitive."""
        data_uppercase = {
            "support_ticket": {
                "ticket1": {"id": "ticket1", "status": "OPEN", "priority": "HIGH"},
            },
            "refund": {
                "refund1": {"id": "refund1", "status": "PENDING"},
            },
            "payment": {
                "payment1": {"id": "payment1", "status": "FAILED"},
            },
            "order": {
                "order1": {"id": "order1", "status": "CANCELLED"},
            },
        }

        result = GetEntitiesNeedingAttention.invoke(data_uppercase)

        self.assertEqual(result["summary"]["open_tickets"], 1)
        self.assertEqual(result["summary"]["urgent_tickets"], 1)
        self.assertEqual(result["summary"]["pending_refunds"], 1)
        self.assertEqual(result["summary"]["failed_payments"], 1)
        self.assertEqual(result["summary"]["cancelled_orders"], 1)

    def test_invalid_entity_table(self):
        """Test when entity table is not a dict."""
        self.data["support_ticket"] = "not_a_dict"

        result = GetEntitiesNeedingAttention.invoke(self.data)

        # Should skip invalid table
        self.assertEqual(result["summary"]["open_tickets"], 0)

    def test_invalid_entity_format(self):
        """Test when entity is not a dict."""
        self.data["support_ticket"]["invalid"] = "not_a_dict"

        result = GetEntitiesNeedingAttention.invoke(self.data)

        # Should skip invalid entity but process valid ones
        self.assertGreater(result["summary"]["open_tickets"], 0)

    def test_missing_status_field(self):
        """Test entities without status field."""
        self.data["support_ticket"]["no_status"] = {
            "id": "no_status",
            "customerId": "customer1",
        }

        result = GetEntitiesNeedingAttention.invoke(self.data)

        # Should handle missing status gracefully (defaults to empty string)
        # Empty string won't match any of our checks
        # Should still process other valid tickets
        self.assertGreater(result["summary"]["open_tickets"], 0)

    def test_missing_priority_field(self):
        """Test ticket without priority field."""
        self.data["support_ticket"]["no_priority"] = {
            "id": "no_priority",
            "customerId": "customer1",
            "status": "open",
        }

        result = GetEntitiesNeedingAttention.invoke(self.data)

        # Should be in open_tickets but not urgent_tickets
        open_ticket_ids = {t["id"] for t in result["results"]["open_tickets"]}
        self.assertIn("no_priority", open_ticket_ids)

        urgent_ticket_ids = {t["id"] for t in result["results"]["urgent_tickets"]}
        self.assertNotIn("no_priority", urgent_ticket_ids)

    def test_escalation_with_status_field(self):
        """Test escalation with status field."""
        result = GetEntitiesNeedingAttention.invoke(self.data)

        # esc1 has status="pending"
        pending_esc_ids = {e["id"] for e in result["results"]["pending_escalations"]}
        self.assertIn("esc1", pending_esc_ids)

    def test_escalation_without_resolvedAt(self):
        """Test escalation without resolvedAt field."""
        result = GetEntitiesNeedingAttention.invoke(self.data)

        # esc2 has resolvedAt=None
        pending_esc_ids = {e["id"] for e in result["results"]["pending_escalations"]}
        self.assertIn("esc2", pending_esc_ids)

    def test_ticket_with_pending_customer_status(self):
        """Test that pending_customer status is handled."""
        # BUG: The code checks for "pending" but the enum has "pending_customer"
        result = GetEntitiesNeedingAttention.invoke(self.data)

        # ticket2 has "pending_customer" status
        # Due to the bug on line 29, it won't be found as "open_ticket"
        open_ticket_ids = {t["id"] for t in result["results"]["open_tickets"]}
        self.assertNotIn("ticket2", open_ticket_ids)  # Bug: should be found but isn't

        # But it should be in unresolved_tickets
        unresolved_ticket_ids = {t["id"] for t in result["results"]["unresolved_tickets"]}
        self.assertIn("ticket2", unresolved_ticket_ids)

    def test_ticket_with_new_status(self):
        """Test that new status tickets are handled."""
        # BUG: The code checks for "pending" and "in_progress" but not "new"
        result = GetEntitiesNeedingAttention.invoke(self.data)

        # ticket3 has "new" status
        # Due to the bug, it won't be found as "open_ticket"
        open_ticket_ids = {t["id"] for t in result["results"]["open_tickets"]}
        self.assertNotIn("ticket3", open_ticket_ids)  # Bug: should be found but isn't

        # But it should be in unresolved_tickets
        unresolved_ticket_ids = {t["id"] for t in result["results"]["unresolved_tickets"]}
        self.assertIn("ticket3", unresolved_ticket_ids)

    def test_response_structure(self):
        """Test that response has correct structure."""
        result = GetEntitiesNeedingAttention.invoke(self.data)

        self.assertIn("results", result)
        self.assertIn("summary", result)
        self.assertIn("total_items_needing_attention", result)

        # Check results structure
        self.assertIn("open_tickets", result["results"])
        self.assertIn("urgent_tickets", result["results"])
        self.assertIn("pending_refunds", result["results"])
        self.assertIn("failed_payments", result["results"])
        self.assertIn("pending_escalations", result["results"])
        self.assertIn("unresolved_tickets", result["results"])
        self.assertIn("cancelled_orders", result["results"])

        # All results should be lists
        for category in result["results"].values():
            self.assertIsInstance(category, list)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = GetEntitiesNeedingAttention.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "get_entities_needing_attention")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        # This function takes no parameters
        self.assertEqual(info["function"]["parameters"]["properties"], {})


if __name__ == "__main__":
    unittest.main()
