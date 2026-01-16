import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_resolve_and_close import ResolveAndClose


class TestResolveAndClose(unittest.TestCase):
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
                    "status": "pending_customer",
                    "priority": "normal",
                    "subject": "Question",
                    "createdAt": "2025-01-12T00:00:00Z",
                    "updatedAt": "2025-01-12T00:00:00Z",
                },
            },
        }

    def test_resolve_and_close_creates_resolution(self):
        """Test that resolving creates a resolution entity."""
        result = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Issued full refund to customer",
        )

        self.assertTrue(result["success"])
        self.assertIn("resolution", result)

        resolution = result["resolution"]
        self.assertIn("id", resolution)
        self.assertTrue(resolution["id"].startswith("res_"))
        self.assertEqual(resolution["type"], "resolution")
        self.assertEqual(resolution["ticketId"], "ticket1")

        # BUG: Line 42 sets "resolutionType" but Resolution model has "outcome" field
        self.assertIn("resolutionType", resolution)  # Bug: wrong field name
        self.assertEqual(resolution["resolutionType"], "refund_issued")

        # BUG: Line 43 sets "description" but Resolution model has "details" field
        self.assertIn("description", resolution)  # Bug: wrong field name
        self.assertEqual(resolution["description"], "Issued full refund to customer")

    def test_resolve_and_close_updates_ticket(self):
        """Test that ticket is updated to resolved status."""
        result = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="technical_fix",
            resolution_notes="Fixed the issue",
        )

        self.assertTrue(result["success"])
        updated_ticket = result["updated_ticket"]

        # Status should be set to resolved
        self.assertEqual(updated_ticket["status"], "resolved")

        # BUG: Line 54 sets "resolvedAt" but SupportTicket has no resolvedAt field
        self.assertIn("resolvedAt", updated_ticket)  # Bug: non-schema field
        self.assertEqual(updated_ticket["resolvedAt"], "2025-01-15T12:00:00Z")

        # updatedAt should be set
        self.assertEqual(updated_ticket["updatedAt"], "2025-01-15T12:00:00Z")

    def test_resolve_and_close_creates_resolution_in_data(self):
        """Test that resolution is added to data."""
        result = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Refund processed",
        )

        resolution_id = result["resolution"]["id"]
        self.assertIn("resolution", self.data)
        self.assertIn(resolution_id, self.data["resolution"])

    def test_resolve_and_close_updates_ticket_in_place(self):
        """Test that ticket in data is updated."""
        result = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="technical_fix",
            resolution_notes="Fixed",
        )

        # Verify ticket in data is updated
        self.assertEqual(self.data["support_ticket"]["ticket1"]["status"], "resolved")

    def test_resolve_and_close_resolution_timestamp(self):
        """Test that resolution has correct timestamp."""
        result = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Refund issued",
        )

        self.assertEqual(result["resolution"]["createdAt"], "2025-01-15T12:00:00Z")

    def test_resolve_and_close_nonexistent_ticket(self):
        """Test with non-existent ticket."""
        result = ResolveAndClose.invoke(
            self.data,
            ticket_id="nonexistent",
            resolution_type="refund_issued",
            resolution_notes="Notes",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_resolve_and_close_invalid_ticket_table(self):
        """Test when ticket table is not a dict."""
        self.data["support_ticket"] = "not_a_dict"

        result = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Notes",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_resolve_and_close_no_ticket_table(self):
        """Test when ticket table doesn't exist."""
        data_without_tickets = {}

        result = ResolveAndClose.invoke(
            data_without_tickets,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Notes",
        )

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

    def test_resolve_and_close_all_resolution_types(self):
        """Test various resolution types."""
        resolution_types = [
            "refund_issued",
            "replacement_sent",
            "technical_fix",
            "policy_override",
            "no_action_needed",
            "troubleshooting_steps",
            "recommendation_provided",
        ]

        for i, res_type in enumerate(resolution_types):
            ticket_id = f"ticket_{i}"
            self.data["support_ticket"][ticket_id] = {
                "id": ticket_id,
                "customerId": "customer1",
                "status": "open",
            }

            result = ResolveAndClose.invoke(
                self.data,
                ticket_id=ticket_id,
                resolution_type=res_type,
                resolution_notes=f"Notes for {res_type}",
            )

            self.assertTrue(result["success"])
            self.assertEqual(result["resolution"]["resolutionType"], res_type)

    def test_resolve_and_close_deterministic_id(self):
        """Test that resolution ID is deterministic."""
        result1 = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Notes",
        )

        # Same params should generate same ID
        result2 = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Notes",
        )

        # IDs should be same (deterministic hash)
        self.assertEqual(result1["resolution"]["id"], result2["resolution"]["id"])

    def test_resolve_and_close_different_tickets_different_ids(self):
        """Test that different tickets get different resolution IDs."""
        result1 = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Notes",
        )

        result2 = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket2",
            resolution_type="refund_issued",
            resolution_notes="Notes",
        )

        self.assertNotEqual(result1["resolution"]["id"], result2["resolution"]["id"])

    def test_resolve_and_close_uses_custom_timestamp(self):
        """Test that custom timestamp is used."""
        self.data["__now"] = "2025-12-31T23:59:59Z"

        result = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Notes",
        )

        self.assertEqual(result["resolution"]["createdAt"], "2025-12-31T23:59:59Z")
        self.assertEqual(result["updated_ticket"]["resolvedAt"], "2025-12-31T23:59:59Z")
        self.assertEqual(result["updated_ticket"]["updatedAt"], "2025-12-31T23:59:59Z")

    def test_resolve_and_close_alternative_timestamp_keys(self):
        """Test alternative timestamp keys."""
        self.data["now"] = "2025-10-01T08:00:00Z"
        self.data.pop("__now")

        result = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Notes",
        )

        self.assertEqual(result["resolution"]["createdAt"], "2025-10-01T08:00:00Z")

    def test_resolve_and_close_defaults_to_constant_timestamp(self):
        """Test that timestamp defaults to constant if not provided."""
        self.data.pop("__now", None)
        self.data.pop("now", None)
        self.data.pop("current_time", None)
        self.data.pop("currentTime", None)

        result = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Notes",
        )

        self.assertEqual(result["resolution"]["createdAt"], "1970-01-01T00:00:00Z")

    def test_resolve_and_close_long_notes(self):
        """Test with long resolution notes."""
        long_notes = "This is a very detailed resolution. " * 100

        result = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes=long_notes,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["resolution"]["description"], long_notes)

    def test_resolve_and_close_creates_resolution_table(self):
        """Test that resolution table is created if it doesn't exist."""
        data_without_resolutions = {
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "status": "open",
                },
            },
        }

        result = ResolveAndClose.invoke(
            data_without_resolutions,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Notes",
        )

        self.assertTrue(result["success"])
        self.assertIn("resolution", data_without_resolutions)
        self.assertIsInstance(data_without_resolutions["resolution"], dict)

    def test_resolve_and_close_invalid_resolution_table(self):
        """Test when existing resolution table is invalid."""
        self.data["resolution"] = "not_a_dict"

        result = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Notes",
        )

        # Should create new dict and succeed
        self.assertTrue(result["success"])
        self.assertIsInstance(self.data["resolution"], dict)

    def test_resolve_and_close_message(self):
        """Test that success message is correct."""
        result = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Notes",
        )

        self.assertIn("message", result)
        self.assertIn("ticket1", result["message"])
        self.assertIn("resolved and closed", result["message"])

    def test_resolve_and_close_preserves_other_ticket_fields(self):
        """Test that other ticket fields are preserved."""
        result = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="Notes",
        )

        ticket = result["updated_ticket"]
        self.assertEqual(ticket["id"], "ticket1")
        self.assertEqual(ticket["customerId"], "customer1")
        self.assertEqual(ticket["priority"], "high")
        self.assertEqual(ticket["subject"], "Defective product")

    def test_resolve_and_close_multiple_resolutions_same_ticket(self):
        """Test creating multiple resolutions for same ticket."""
        result1 = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="refund_issued",
            resolution_notes="First resolution",
        )

        result2 = ResolveAndClose.invoke(
            self.data,
            ticket_id="ticket1",
            resolution_type="replacement_sent",
            resolution_notes="Second resolution",
        )

        # Different resolution types should create different IDs
        self.assertNotEqual(result1["resolution"]["id"], result2["resolution"]["id"])

        # Both should be in data
        self.assertEqual(len(self.data["resolution"]), 2)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = ResolveAndClose.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "resolve_and_close")
        self.assertIn("description", info["function"])
        self.assertIn("CRITICAL", info["function"]["description"])
        self.assertIn("parameters", info["function"])
        self.assertIn("ticket_id", info["function"]["parameters"]["properties"])
        self.assertIn("resolution_type", info["function"]["parameters"]["properties"])
        self.assertIn("resolution_notes", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("ticket_id", required)
        self.assertIn("resolution_type", required)
        self.assertIn("resolution_notes", required)


if __name__ == "__main__":
    unittest.main()
