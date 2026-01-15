import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_escalate_ticket import EscalateTicket


class TestEscalateTicket(unittest.TestCase):
    def setUp(self):
        """Set up test data with support tickets."""
        self.data: Dict[str, Any] = {
            "__now": "2025-01-15T12:00:00Z",
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "status": "open",
                    "priority": "high",
                    "subject": "Defective product",
                    "createdAt": "2025-01-10T00:00:00Z",
                    "updatedAt": "2025-01-10T00:00:00Z",
                },
                "ticket2": {
                    "id": "ticket2",
                    "customerId": "customer2",
                    "status": "new",
                    "priority": "normal",
                    "subject": "Question about order",
                    "createdAt": "2025-01-12T00:00:00Z",
                    "updatedAt": "2025-01-12T00:00:00Z",
                },
            },
        }

    def test_escalate_ticket_basic(self):
        """Test creating a basic escalation."""
        result = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering_team",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Ticket ticket1 escalated to engineering_team")

        # Check escalation structure
        escalation = result["escalation"]
        self.assertIn("id", escalation)
        self.assertTrue(escalation["id"].startswith("esc_"))
        self.assertEqual(escalation["type"], "escalation")
        self.assertEqual(escalation["ticketId"], "ticket1")
        self.assertEqual(escalation["escalationType"], "technical")
        self.assertEqual(escalation["destination"], "engineering_team")
        self.assertEqual(escalation["notes"], "")
        self.assertEqual(escalation["createdAt"], "2025-01-15T12:00:00Z")
        self.assertIsNone(escalation["resolvedAt"])

        # BUG: Line 47 sets status="pending", but Escalation model has no status field
        self.assertIn("status", escalation)  # Bug: non-schema field
        self.assertEqual(escalation["status"], "pending")

        # Check that escalation was added to data
        self.assertIn("escalation", self.data)
        self.assertIn(escalation["id"], self.data["escalation"])

    def test_escalate_ticket_with_notes(self):
        """Test creating an escalation with notes."""
        result = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="policy_exception",
            destination="management",
            notes="High-value customer needs special handling",
        )

        self.assertTrue(result["success"])
        escalation = result["escalation"]
        self.assertEqual(escalation["notes"], "High-value customer needs special handling")
        self.assertEqual(escalation["escalationType"], "policy_exception")
        self.assertEqual(escalation["destination"], "management")

    def test_escalate_ticket_product_specialist(self):
        """Test escalating to product specialist."""
        result = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket2",
            escalation_type="product_specialist",
            destination="product_team",
            notes="Needs product expertise",
        )

        self.assertTrue(result["success"])
        escalation = result["escalation"]
        self.assertEqual(escalation["escalationType"], "product_specialist")
        self.assertEqual(escalation["destination"], "product_team")

    def test_escalate_nonexistent_ticket(self):
        """Test escalating non-existent ticket."""
        result = EscalateTicket.invoke(
            self.data,
            ticket_id="nonexistent",
            escalation_type="technical",
            destination="engineering",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_escalate_multiple_times_same_ticket(self):
        """Test escalating the same ticket multiple times."""
        # First escalation
        result1 = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        # Second escalation
        result2 = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="policy_exception",
            destination="management",
        )

        self.assertTrue(result1["success"])
        self.assertTrue(result2["success"])

        # Both should have different IDs
        self.assertNotEqual(result1["escalation"]["id"], result2["escalation"]["id"])

        # Both should be in data
        self.assertEqual(len(self.data["escalation"]), 2)

    def test_escalate_deterministic_id_generation(self):
        """Test that escalation ID is deterministic based on input."""
        result1 = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        # Create another escalation with same params (would get same hash if timestamp is same)
        result2 = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        # IDs should be deterministic based on ticket_id, escalation_type, and destination
        # Since input is same, hash should be same
        self.assertEqual(result1["escalation"]["id"], result2["escalation"]["id"])

    def test_escalate_creates_escalation_table(self):
        """Test that escalation table is created if it doesn't exist."""
        data_without_escalations = {
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "status": "open",
                },
            },
        }

        result = EscalateTicket.invoke(
            data_without_escalations,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        self.assertTrue(result["success"])
        self.assertIn("escalation", data_without_escalations)
        self.assertIsInstance(data_without_escalations["escalation"], dict)

    def test_escalate_invalid_ticket_table(self):
        """Test when ticket table is not a dict."""
        self.data["support_ticket"] = "not_a_dict"

        result = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_escalate_no_ticket_table(self):
        """Test when ticket table doesn't exist."""
        data_without_tickets = {}

        result = EscalateTicket.invoke(
            data_without_tickets,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_escalate_empty_notes(self):
        """Test with empty notes string."""
        result = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
            notes="",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["escalation"]["notes"], "")

    def test_escalate_default_notes(self):
        """Test that notes defaults to empty string."""
        result = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["escalation"]["notes"], "")

    def test_escalate_uses_custom_timestamp(self):
        """Test that custom timestamp is used."""
        self.data["__now"] = "2025-12-31T23:59:59Z"

        result = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["escalation"]["createdAt"], "2025-12-31T23:59:59Z")

    def test_escalate_uses_alternative_timestamp_keys(self):
        """Test alternative timestamp keys."""
        # Test with "now" key
        self.data["now"] = "2025-10-01T08:00:00Z"
        self.data.pop("__now")

        result = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        self.assertEqual(result["escalation"]["createdAt"], "2025-10-01T08:00:00Z")

    def test_escalate_defaults_to_constant_timestamp(self):
        """Test that timestamp defaults to constant if not provided."""
        # Remove all timestamp keys
        self.data.pop("__now", None)
        self.data.pop("now", None)
        self.data.pop("current_time", None)
        self.data.pop("currentTime", None)

        result = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["escalation"]["createdAt"], "1970-01-01T00:00:00Z")

    def test_escalate_preserves_existing_escalations(self):
        """Test that existing escalations are preserved."""
        # Add existing escalation
        self.data["escalation"] = {
            "existing_esc": {
                "id": "existing_esc",
                "ticketId": "ticket2",
                "escalationType": "old",
            }
        }

        result = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        self.assertTrue(result["success"])
        # Should have 2 escalations now
        self.assertEqual(len(self.data["escalation"]), 2)
        self.assertIn("existing_esc", self.data["escalation"])
        self.assertIn(result["escalation"]["id"], self.data["escalation"])

    def test_escalate_all_escalation_types(self):
        """Test all valid escalation types."""
        escalation_types = ["technical", "policy_exception", "product_specialist"]

        for i, esc_type in enumerate(escalation_types):
            result = EscalateTicket.invoke(
                self.data,
                ticket_id="ticket1",
                escalation_type=esc_type,
                destination=f"team_{i}",
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["escalation"]["escalationType"], esc_type)

    def test_escalate_long_notes(self):
        """Test with long notes."""
        long_notes = "This is a very long note. " * 100

        result = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
            notes=long_notes,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["escalation"]["notes"], long_notes)

    def test_escalate_special_characters_in_destination(self):
        """Test with special characters in destination."""
        result = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="team@email.com",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["escalation"]["destination"], "team@email.com")

    def test_escalate_mutates_data_in_place(self):
        """Test that the tool mutates data in place."""
        initial_escalation_count = len(self.data.get("escalation", {}))

        EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        self.assertEqual(len(self.data["escalation"]), initial_escalation_count + 1)

    def test_escalate_invalid_escalation_table(self):
        """Test when existing escalation table is invalid type."""
        self.data["escalation"] = "not_a_dict"

        result = EscalateTicket.invoke(
            self.data,
            ticket_id="ticket1",
            escalation_type="technical",
            destination="engineering",
        )

        # Should create new dict and succeed
        self.assertTrue(result["success"])
        self.assertIsInstance(self.data["escalation"], dict)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = EscalateTicket.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "escalate_ticket")
        self.assertIn("description", info["function"])
        self.assertIn("CRITICAL", info["function"]["description"])  # Warning about verification
        self.assertIn("parameters", info["function"])
        self.assertIn("ticket_id", info["function"]["parameters"]["properties"])
        self.assertIn("escalation_type", info["function"]["parameters"]["properties"])
        self.assertIn("destination", info["function"]["parameters"]["properties"])
        self.assertIn("notes", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("ticket_id", required)
        self.assertIn("escalation_type", required)
        self.assertIn("destination", required)
        self.assertNotIn("notes", required)  # notes is optional


if __name__ == "__main__":
    unittest.main()
