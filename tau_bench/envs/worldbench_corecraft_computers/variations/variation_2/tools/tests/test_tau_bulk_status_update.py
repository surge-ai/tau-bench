import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_bulk_status_update import BulkStatusUpdate


class TestBulkStatusUpdate(unittest.TestCase):
    def setUp(self):
        """Set up test data with various entities."""
        self.data: Dict[str, Any] = {
            "__now": "2025-01-15T12:00:00Z",
            "order": {
                "order1": {
                    "id": "order1",
                    "customerId": "customer1",
                    "status": "pending",
                    "createdAt": "2025-01-10T00:00:00Z",
                    "updatedAt": "2025-01-10T00:00:00Z",
                },
                "order2": {
                    "id": "order2",
                    "customerId": "customer2",
                    "status": "pending",
                    "createdAt": "2025-01-11T00:00:00Z",
                    "updatedAt": "2025-01-11T00:00:00Z",
                },
                "order3": {
                    "id": "order3",
                    "customerId": "customer3",
                    "status": "paid",
                    "createdAt": "2025-01-12T00:00:00Z",
                    "updatedAt": "2025-01-12T00:00:00Z",
                },
            },
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "status": "new",
                    "priority": "high",
                    "createdAt": "2025-01-10T00:00:00Z",
                    "updatedAt": "2025-01-10T00:00:00Z",
                },
                "ticket2": {
                    "id": "ticket2",
                    "customerId": "customer2",
                    "status": "open",
                    "priority": "normal",
                    "createdAt": "2025-01-11T00:00:00Z",
                    "updatedAt": "2025-01-11T00:00:00Z",
                },
            },
            "payment": {
                "payment1": {
                    "id": "payment1",
                    "orderId": "order1",
                    "amount": 100.0,
                    "status": "pending",
                    "createdAt": "2025-01-10T00:00:00Z",
                    "processedAt": None,
                },
                "payment2": {
                    "id": "payment2",
                    "orderId": "order2",
                    "amount": 200.0,
                    "status": "authorized",
                    "createdAt": "2025-01-11T00:00:00Z",
                    "processedAt": None,
                },
            },
            "shipment": {
                "shipment1": {
                    "id": "shipment1",
                    "orderId": "order1",
                    "carrier": "ups_ground",
                    "status": "label_created",
                    "createdAt": "2025-01-10T00:00:00Z",
                },
                "shipment2": {
                    "id": "shipment2",
                    "orderId": "order2",
                    "carrier": "fedex_express",
                    "status": "in_transit",
                    "createdAt": "2025-01-11T00:00:00Z",
                },
            },
        }

    def test_bulk_update_orders(self):
        """Test bulk updating order statuses."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="order",
            entity_ids=["order1", "order2"],
            status="paid",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["entity_type"], "order")
        self.assertEqual(result["status"], "paid")
        self.assertEqual(result["summary"]["updated"], 2)
        self.assertEqual(result["summary"]["not_found"], 0)
        self.assertEqual(result["summary"]["errors"], 0)

        # Verify orders were updated
        self.assertEqual(self.data["order"]["order1"]["status"], "paid")
        self.assertEqual(self.data["order"]["order2"]["status"], "paid")

        # Verify updatedAt was set
        self.assertEqual(self.data["order"]["order1"]["updatedAt"], "2025-01-15T12:00:00Z")
        self.assertEqual(self.data["order"]["order2"]["updatedAt"], "2025-01-15T12:00:00Z")

    def test_bulk_update_tickets(self):
        """Test bulk updating ticket statuses."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="ticket",
            entity_ids=["ticket1", "ticket2"],
            status="resolved",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["entity_type"], "ticket")
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["summary"]["updated"], 2)

        # Verify tickets were updated
        self.assertEqual(self.data["support_ticket"]["ticket1"]["status"], "resolved")
        self.assertEqual(self.data["support_ticket"]["ticket2"]["status"], "resolved")

        # BUG: Line 66 checks `if data_key in ["ticket", "support_ticket"]`
        # but data_key is always "support_ticket" after normalization, so "ticket" never matches
        # This means the resolvedAt field logic is actually working by accident

        # BUG: Line 68 sets resolvedAt field, but SupportTicket model doesn't have this field
        # The following assertion documents this bug:
        self.assertIn("resolvedAt", self.data["support_ticket"]["ticket1"])  # Bug: non-schema field

    def test_bulk_update_payments(self):
        """Test bulk updating payment statuses."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="payment",
            entity_ids=["payment1", "payment2"],
            status="captured",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["summary"]["updated"], 2)

        # Verify payments were updated
        self.assertEqual(self.data["payment"]["payment1"]["status"], "captured")
        self.assertEqual(self.data["payment"]["payment2"]["status"], "captured")

        # Payments don't have updatedAt field, so it shouldn't be set
        self.assertNotIn("updatedAt", self.data["payment"]["payment1"])

    def test_bulk_update_payment_completed_status(self):
        """Test that completed status sets completedAt field."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="payment",
            entity_ids=["payment1"],
            status="completed",
        )

        self.assertTrue(result["success"])
        self.assertEqual(self.data["payment"]["payment1"]["status"], "completed")

        # BUG: Line 72 sets completedAt field, but Payment model doesn't have this field
        # Payment has "processedAt" instead
        self.assertIn("completedAt", self.data["payment"]["payment1"])  # Bug: non-schema field
        self.assertEqual(self.data["payment"]["payment1"]["completedAt"], "2025-01-15T12:00:00Z")

    def test_bulk_update_payment_failed_status(self):
        """Test that failed status sets failedAt field."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="payment",
            entity_ids=["payment1"],
            status="failed",
        )

        self.assertTrue(result["success"])
        self.assertEqual(self.data["payment"]["payment1"]["status"], "failed")

        # BUG: Line 74 sets failedAt field, but Payment model doesn't have this field
        self.assertIn("failedAt", self.data["payment"]["payment1"])  # Bug: non-schema field
        self.assertEqual(self.data["payment"]["payment1"]["failedAt"], "2025-01-15T12:00:00Z")

    def test_bulk_update_shipments(self):
        """Test bulk updating shipment statuses."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="shipment",
            entity_ids=["shipment1", "shipment2"],
            status="out_for_delivery",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["summary"]["updated"], 2)

        # Verify shipments were updated
        self.assertEqual(self.data["shipment"]["shipment1"]["status"], "out_for_delivery")
        self.assertEqual(self.data["shipment"]["shipment2"]["status"], "out_for_delivery")

    def test_bulk_update_shipment_delivered_status(self):
        """Test that delivered status sets deliveredAt field."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="shipment",
            entity_ids=["shipment1"],
            status="delivered",
        )

        self.assertTrue(result["success"])
        self.assertEqual(self.data["shipment"]["shipment1"]["status"], "delivered")

        # BUG: Line 78 sets deliveredAt field, but Shipment model doesn't have this field
        self.assertIn("deliveredAt", self.data["shipment"]["shipment1"])  # Bug: non-schema field
        self.assertEqual(self.data["shipment"]["shipment1"]["deliveredAt"], "2025-01-15T12:00:00Z")

    def test_bulk_update_ticket_closed_status(self):
        """Test that closed status sets resolvedAt field."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="ticket",
            entity_ids=["ticket1"],
            status="closed",
        )

        self.assertTrue(result["success"])
        self.assertEqual(self.data["support_ticket"]["ticket1"]["status"], "closed")

        # BUG: resolvedAt field is set, but not in SupportTicket schema
        self.assertIn("resolvedAt", self.data["support_ticket"]["ticket1"])  # Bug: non-schema field

    def test_bulk_update_not_found_entities(self):
        """Test handling of non-existent entities."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="order",
            entity_ids=["order1", "nonexistent1", "order2", "nonexistent2"],
            status="paid",
        )

        self.assertTrue(result["success"])  # Still successful if at least one was updated
        self.assertEqual(result["summary"]["updated"], 2)
        self.assertEqual(result["summary"]["not_found"], 2)
        self.assertEqual(len(result["results"]["not_found"]), 2)
        self.assertIn("nonexistent1", result["results"]["not_found"])
        self.assertIn("nonexistent2", result["results"]["not_found"])

    def test_bulk_update_all_not_found(self):
        """Test when all entities are not found."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="order",
            entity_ids=["nonexistent1", "nonexistent2"],
            status="paid",
        )

        self.assertFalse(result["success"])  # No updates
        self.assertEqual(result["summary"]["updated"], 0)
        self.assertEqual(result["summary"]["not_found"], 2)

    def test_bulk_update_invalid_entity_type(self):
        """Test with invalid entity type."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="invalid_type",
            entity_ids=["entity1"],
            status="active",
        )

        self.assertIn("error", result)
        self.assertIn("Unknown entity type", result["error"])

    def test_bulk_update_empty_entity_ids(self):
        """Test with empty entity ID list."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="order",
            entity_ids=[],
            status="paid",
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["summary"]["total"], 0)
        self.assertEqual(result["summary"]["updated"], 0)

    def test_bulk_update_entity_type_alias(self):
        """Test that entity type aliases work (e.g., 'ticket' -> 'support_ticket')."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="ticket",  # Using alias
            entity_ids=["ticket1"],
            status="resolved",
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["entity_type"], "ticket")  # Original type preserved in response
        self.assertEqual(self.data["support_ticket"]["ticket1"]["status"], "resolved")

    def test_bulk_update_support_ticket_full_name(self):
        """Test using full entity type name."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="support_ticket",
            entity_ids=["ticket1"],
            status="resolved",
        )

        self.assertTrue(result["success"])
        self.assertEqual(self.data["support_ticket"]["ticket1"]["status"], "resolved")

    def test_bulk_update_preserves_old_status(self):
        """Test that old status is preserved in results."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="order",
            entity_ids=["order1", "order3"],
            status="fulfilled",
        )

        self.assertEqual(len(result["results"]["updated"]), 2)

        # Find the result for order1
        order1_result = next(r for r in result["results"]["updated"] if r["id"] == "order1")
        self.assertEqual(order1_result["old_status"], "pending")
        self.assertEqual(order1_result["new_status"], "fulfilled")

        # Find the result for order3
        order3_result = next(r for r in result["results"]["updated"] if r["id"] == "order3")
        self.assertEqual(order3_result["old_status"], "paid")
        self.assertEqual(order3_result["new_status"], "fulfilled")

    def test_bulk_update_invalid_entity_format(self):
        """Test handling of invalid entity format."""
        self.data["order"]["invalid_order"] = "not_a_dict"

        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="order",
            entity_ids=["order1", "invalid_order"],
            status="paid",
        )

        self.assertTrue(result["success"])  # order1 was updated
        self.assertEqual(result["summary"]["updated"], 1)
        self.assertEqual(result["summary"]["errors"], 1)
        self.assertEqual(len(result["results"]["errors"]), 1)
        self.assertEqual(result["results"]["errors"][0]["id"], "invalid_order")

    def test_bulk_update_no_data_table(self):
        """Test when entity table doesn't exist."""
        data_without_orders = {"support_ticket": {}}

        result = BulkStatusUpdate.invoke(
            data_without_orders,
            entity_type="order",
            entity_ids=["order1"],
            status="paid",
        )

        self.assertIn("error", result)
        self.assertIn("No order data available", result["error"])

    def test_bulk_update_non_dict_entity_table(self):
        """Test when entity table is not a dict."""
        self.data["order"] = "not_a_dict"

        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="order",
            entity_ids=["order1"],
            status="paid",
        )

        self.assertIn("error", result)
        self.assertIn("No order data available", result["error"])

    def test_bulk_update_uses_custom_timestamp(self):
        """Test that custom timestamp is used for updatedAt."""
        self.data["__now"] = "2025-12-31T23:59:59Z"

        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="order",
            entity_ids=["order1"],
            status="paid",
        )

        self.assertTrue(result["success"])
        self.assertEqual(self.data["order"]["order1"]["updatedAt"], "2025-12-31T23:59:59Z")

    def test_bulk_update_only_updates_entities_with_updatedAt(self):
        """Test that updatedAt is only set on entities that have this field."""
        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="payment",
            entity_ids=["payment1"],
            status="captured",
        )

        self.assertTrue(result["success"])
        # Payment doesn't have updatedAt in schema
        self.assertNotIn("updatedAt", self.data["payment"]["payment1"])

    def test_bulk_update_doesnt_set_resolvedAt_twice(self):
        """Test that resolvedAt is not overwritten if already set."""
        # Pre-set resolvedAt on ticket1
        self.data["support_ticket"]["ticket1"]["resolvedAt"] = "2025-01-01T00:00:00Z"

        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="ticket",
            entity_ids=["ticket1"],
            status="resolved",
        )

        self.assertTrue(result["success"])
        # Should not overwrite existing resolvedAt
        self.assertEqual(
            self.data["support_ticket"]["ticket1"]["resolvedAt"],
            "2025-01-01T00:00:00Z"
        )

    def test_bulk_update_doesnt_set_completedAt_twice(self):
        """Test that completedAt is not overwritten if already set."""
        # Pre-set completedAt on payment1
        self.data["payment"]["payment1"]["completedAt"] = "2025-01-01T00:00:00Z"

        result = BulkStatusUpdate.invoke(
            self.data,
            entity_type="payment",
            entity_ids=["payment1"],
            status="completed",
        )

        self.assertTrue(result["success"])
        # Should not overwrite existing completedAt
        self.assertEqual(
            self.data["payment"]["payment1"]["completedAt"],
            "2025-01-01T00:00:00Z"
        )

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = BulkStatusUpdate.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "bulk_status_update")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("entity_type", info["function"]["parameters"]["properties"])
        self.assertIn("entity_ids", info["function"]["parameters"]["properties"])
        self.assertIn("status", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])


if __name__ == "__main__":
    unittest.main()
