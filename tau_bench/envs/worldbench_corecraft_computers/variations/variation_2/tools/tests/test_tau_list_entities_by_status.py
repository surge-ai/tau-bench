import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_list_entities_by_status import ListEntitiesByStatus


class TestListEntitiesByStatus(unittest.TestCase):
    def setUp(self):
        """Set up test data with various entities having different statuses."""
        self.data: Dict[str, Any] = {
            "order": {
                "order1": {"id": "order1", "customerId": "customer1", "status": "pending"},
                "order2": {"id": "order2", "customerId": "customer2", "status": "paid"},
                "order3": {"id": "order3", "customerId": "customer3", "status": "paid"},
                "order4": {"id": "order4", "customerId": "customer4", "status": "fulfilled"},
                "order5": {"id": "order5", "customerId": "customer5", "status": "cancelled"},
            },
            "support_ticket": {
                "ticket1": {"id": "ticket1", "customerId": "customer1", "status": "new"},
                "ticket2": {"id": "ticket2", "customerId": "customer2", "status": "open"},
                "ticket3": {"id": "ticket3", "customerId": "customer3", "status": "open"},
                "ticket4": {"id": "ticket4", "customerId": "customer4", "status": "resolved"},
                "ticket5": {"id": "ticket5", "customerId": "customer5", "status": "closed"},
            },
            "payment": {
                "payment1": {"id": "payment1", "orderId": "order1", "status": "pending"},
                "payment2": {"id": "payment2", "orderId": "order2", "status": "captured"},
                "payment3": {"id": "payment3", "orderId": "order3", "status": "captured"},
                "payment4": {"id": "payment4", "orderId": "order4", "status": "failed"},
            },
            "shipment": {
                "shipment1": {"id": "shipment1", "orderId": "order1", "status": "label_created"},
                "shipment2": {"id": "shipment2", "orderId": "order2", "status": "in_transit"},
                "shipment3": {"id": "shipment3", "orderId": "order3", "status": "delivered"},
            },
            "refund": {
                "refund1": {"id": "refund1", "paymentId": "payment1", "status": "pending"},
                "refund2": {"id": "refund2", "paymentId": "payment2", "status": "approved"},
                "refund3": {"id": "refund3", "paymentId": "payment3", "status": "processed"},
            },
        }

    def test_list_orders_by_status(self):
        """Test listing orders grouped by status."""
        result = ListEntitiesByStatus.invoke(self.data, entity_type="order")

        self.assertEqual(result["entity_type"], "order")
        self.assertEqual(result["total"], 5)

        # Check status counts
        self.assertEqual(result["status_counts"]["pending"], 1)
        self.assertEqual(result["status_counts"]["paid"], 2)
        self.assertEqual(result["status_counts"]["fulfilled"], 1)
        self.assertEqual(result["status_counts"]["cancelled"], 1)

        # Check grouped entities
        self.assertEqual(len(result["by_status"]["pending"]), 1)
        self.assertEqual(len(result["by_status"]["paid"]), 2)
        self.assertEqual(result["by_status"]["paid"][0]["id"], "order2")
        self.assertEqual(result["by_status"]["paid"][1]["id"], "order3")

    def test_list_tickets_by_status(self):
        """Test listing tickets grouped by status."""
        result = ListEntitiesByStatus.invoke(self.data, entity_type="ticket")

        self.assertEqual(result["entity_type"], "ticket")
        self.assertEqual(result["total"], 5)

        # Check status counts
        self.assertEqual(result["status_counts"]["new"], 1)
        self.assertEqual(result["status_counts"]["open"], 2)
        self.assertEqual(result["status_counts"]["resolved"], 1)
        self.assertEqual(result["status_counts"]["closed"], 1)

    def test_list_payments_by_status(self):
        """Test listing payments grouped by status."""
        result = ListEntitiesByStatus.invoke(self.data, entity_type="payment")

        self.assertEqual(result["entity_type"], "payment")
        self.assertEqual(result["total"], 4)

        self.assertEqual(result["status_counts"]["pending"], 1)
        self.assertEqual(result["status_counts"]["captured"], 2)
        self.assertEqual(result["status_counts"]["failed"], 1)

    def test_list_shipments_by_status(self):
        """Test listing shipments grouped by status."""
        result = ListEntitiesByStatus.invoke(self.data, entity_type="shipment")

        self.assertEqual(result["entity_type"], "shipment")
        self.assertEqual(result["total"], 3)

        self.assertEqual(result["status_counts"]["label_created"], 1)
        self.assertEqual(result["status_counts"]["in_transit"], 1)
        self.assertEqual(result["status_counts"]["delivered"], 1)

    def test_list_refunds_by_status(self):
        """Test listing refunds grouped by status."""
        result = ListEntitiesByStatus.invoke(self.data, entity_type="refund")

        self.assertEqual(result["entity_type"], "refund")
        self.assertEqual(result["total"], 3)

        self.assertEqual(result["status_counts"]["pending"], 1)
        self.assertEqual(result["status_counts"]["approved"], 1)
        self.assertEqual(result["status_counts"]["processed"], 1)

    def test_list_entity_type_alias(self):
        """Test that entity type aliases work."""
        result = ListEntitiesByStatus.invoke(self.data, entity_type="ticket")

        self.assertEqual(result["entity_type"], "ticket")
        self.assertEqual(result["total"], 5)

    def test_list_support_ticket_full_name(self):
        """Test using full entity type name."""
        result = ListEntitiesByStatus.invoke(self.data, entity_type="support_ticket")

        self.assertEqual(result["entity_type"], "support_ticket")
        self.assertEqual(result["total"], 5)

    def test_list_unknown_entity_type(self):
        """Test with unknown entity type."""
        result = ListEntitiesByStatus.invoke(self.data, entity_type="invalid_type")

        self.assertIn("error", result)
        self.assertIn("Unknown entity type", result["error"])

    def test_list_empty_entity_table(self):
        """Test with empty entity table."""
        data_with_empty = {"order": {}}

        result = ListEntitiesByStatus.invoke(data_with_empty, entity_type="order")

        self.assertEqual(result["by_status"], {})
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["status_counts"], {})

    def test_list_no_entity_table(self):
        """Test when entity table doesn't exist."""
        data_without_orders = {"support_ticket": {}}

        result = ListEntitiesByStatus.invoke(data_without_orders, entity_type="order")

        self.assertEqual(result["by_status"], {})
        self.assertEqual(result["total"], 0)

    def test_list_non_dict_entity_table(self):
        """Test when entity table is not a dict."""
        self.data["order"] = "not_a_dict"

        result = ListEntitiesByStatus.invoke(self.data, entity_type="order")

        self.assertEqual(result["by_status"], {})
        self.assertEqual(result["total"], 0)

    def test_list_entities_without_status_field(self):
        """Test handling entities without status field."""
        self.data["order"]["order6"] = {"id": "order6", "customerId": "customer6"}

        result = ListEntitiesByStatus.invoke(self.data, entity_type="order")

        # Should group under "unknown"
        self.assertIn("unknown", result["by_status"])
        self.assertEqual(len(result["by_status"]["unknown"]), 1)
        self.assertEqual(result["by_status"]["unknown"][0]["id"], "order6")

    def test_list_invalid_entity_format(self):
        """Test when entity is not a dict."""
        self.data["order"]["invalid"] = "not_a_dict"

        result = ListEntitiesByStatus.invoke(self.data, entity_type="order")

        # Should skip invalid entity
        self.assertEqual(result["total"], 5)  # Only valid entities

    def test_list_complete_entity_objects_returned(self):
        """Test that complete entity objects are returned."""
        result = ListEntitiesByStatus.invoke(self.data, entity_type="order")

        # Check that full objects are returned
        paid_orders = result["by_status"]["paid"]
        self.assertIn("id", paid_orders[0])
        self.assertIn("customerId", paid_orders[0])
        self.assertIn("status", paid_orders[0])

    def test_list_status_counts_matches_entities(self):
        """Test that status counts match the number of entities in each group."""
        result = ListEntitiesByStatus.invoke(self.data, entity_type="order")

        for status, count in result["status_counts"].items():
            self.assertEqual(len(result["by_status"][status]), count)

    def test_list_total_matches_sum_of_counts(self):
        """Test that total matches sum of all status counts."""
        result = ListEntitiesByStatus.invoke(self.data, entity_type="order")

        total_from_counts = sum(result["status_counts"].values())
        self.assertEqual(result["total"], total_from_counts)

    def test_list_all_valid_entity_types(self):
        """Test all valid entity types."""
        entity_types = ["order", "ticket", "support_ticket", "payment", "shipment", "refund"]

        for entity_type in entity_types:
            result = ListEntitiesByStatus.invoke(self.data, entity_type=entity_type)

            # Should not error
            self.assertIn("by_status", result)
            self.assertIn("status_counts", result)
            self.assertIn("total", result)

    def test_list_preserves_status_values(self):
        """Test that original status values are preserved."""
        result = ListEntitiesByStatus.invoke(self.data, entity_type="order")

        # Check that status values match what's in data
        for status, entities in result["by_status"].items():
            for entity in entities:
                self.assertEqual(entity["status"], status)

    def test_list_case_preserves_status(self):
        """Test that status is stored as-is (case preserved)."""
        self.data["order"]["order_upper"] = {
            "id": "order_upper",
            "status": "PAID",  # Uppercase
        }

        result = ListEntitiesByStatus.invoke(self.data, entity_type="order")

        # Should create separate group for uppercase
        self.assertIn("PAID", result["by_status"])
        self.assertEqual(len(result["by_status"]["PAID"]), 1)

    def test_list_response_structure(self):
        """Test that response has correct structure."""
        result = ListEntitiesByStatus.invoke(self.data, entity_type="order")

        self.assertIn("entity_type", result)
        self.assertIn("by_status", result)
        self.assertIn("status_counts", result)
        self.assertIn("total", result)

        self.assertIsInstance(result["by_status"], dict)
        self.assertIsInstance(result["status_counts"], dict)
        self.assertIsInstance(result["total"], int)

        # Each status group should be a list
        for entities in result["by_status"].values():
            self.assertIsInstance(entities, list)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = ListEntitiesByStatus.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "list_entities_by_status")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("entity_type", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("entity_type", info["function"]["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()
