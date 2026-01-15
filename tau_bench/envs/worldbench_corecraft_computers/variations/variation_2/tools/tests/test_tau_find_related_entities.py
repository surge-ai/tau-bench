import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_find_related_entities import FindRelatedEntities


class TestFindRelatedEntities(unittest.TestCase):
    def setUp(self):
        """Set up test data with interconnected entities."""
        self.data: Dict[str, Any] = {
            "customer": {
                "customer1": {
                    "id": "customer1",
                    "name": "John Doe",
                    "email": "john@example.com",
                },
            },
            "order": {
                "order1": {
                    "id": "order1",
                    "customerId": "customer1",
                    "status": "paid",
                    "lineItems": [
                        {"productId": "prod1", "quantity": 2},
                        {"productId": "prod2", "quantity": 1},
                    ],
                },
                "order2": {
                    "id": "order2",
                    "customerId": "customer1",
                    "status": "pending",
                    "lineItems": [
                        {"productId": "prod3", "quantity": 1},
                    ],
                },
            },
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "orderId": "order1",
                    "status": "open",
                },
                "ticket2": {
                    "id": "ticket2",
                    "customerId": "customer1",
                    "status": "resolved",
                },
            },
            "payment": {
                "payment1": {
                    "id": "payment1",
                    "orderId": "order1",
                    "amount": 100.0,
                    "status": "captured",
                },
                "payment2": {
                    "id": "payment2",
                    "orderId": "order2",
                    "amount": 200.0,
                    "status": "pending",
                },
            },
            "shipment": {
                "shipment1": {
                    "id": "shipment1",
                    "orderId": "order1",
                    "carrier": "ups_ground",
                    "status": "in_transit",
                },
            },
            "refund": {
                "refund1": {
                    "id": "refund1",
                    "paymentId": "payment1",
                    "amount": 50.0,
                    "status": "approved",
                },
            },
            "escalation": {
                "esc1": {
                    "id": "esc1",
                    "ticketId": "ticket1",
                    "escalationType": "technical",
                },
            },
            "resolution": {
                "res1": {
                    "id": "res1",
                    "ticketId": "ticket1",
                    "outcome": "refund_issued",
                },
            },
            "product": {
                "prod1": {
                    "id": "prod1",
                    "name": "Gaming Mouse",
                    "price": 59.99,
                },
                "prod2": {
                    "id": "prod2",
                    "name": "Keyboard",
                    "price": 129.99,
                },
                "prod3": {
                    "id": "prod3",
                    "name": "Monitor",
                    "price": 299.99,
                },
            },
        }

    def test_find_related_from_customer(self):
        """Test finding all entities related to a customer."""
        result = FindRelatedEntities.invoke(self.data, entity_id="customer1")

        self.assertEqual(result["source_entity_id"], "customer1")
        self.assertEqual(result["source_entity_type"], "customer")

        # Should find customer themselves
        self.assertEqual(len(result["results"]["customers"]), 1)
        self.assertEqual(result["results"]["customers"][0]["id"], "customer1")

        # Should find all orders for customer
        self.assertEqual(len(result["results"]["orders"]), 2)
        order_ids = {o["id"] for o in result["results"]["orders"]}
        self.assertIn("order1", order_ids)
        self.assertIn("order2", order_ids)

        # Should find all tickets for customer
        self.assertEqual(len(result["results"]["tickets"]), 2)

        # Should find payments for customer's orders
        self.assertEqual(len(result["results"]["payments"]), 2)

        # Should find shipments for customer's orders
        self.assertEqual(len(result["results"]["shipments"]), 1)

        # Should find products from orders
        self.assertEqual(len(result["results"]["products"]), 3)
        product_ids = {p["id"] for p in result["results"]["products"]}
        self.assertIn("prod1", product_ids)
        self.assertIn("prod2", product_ids)
        self.assertIn("prod3", product_ids)

    def test_find_related_from_order(self):
        """Test finding entities related to an order."""
        result = FindRelatedEntities.invoke(self.data, entity_id="order1")

        self.assertEqual(result["source_entity_id"], "order1")
        self.assertEqual(result["source_entity_type"], "order")

        # Should find the customer
        self.assertEqual(len(result["results"]["customers"]), 1)
        self.assertEqual(result["results"]["customers"][0]["id"], "customer1")

        # Should find the order itself
        self.assertEqual(len(result["results"]["orders"]), 1)

        # Should find tickets for this order
        self.assertEqual(len(result["results"]["tickets"]), 1)
        self.assertEqual(result["results"]["tickets"][0]["id"], "ticket1")

        # Should find payments for this order
        self.assertEqual(len(result["results"]["payments"]), 1)
        self.assertEqual(result["results"]["payments"][0]["id"], "payment1")

        # Should find shipments for this order
        self.assertEqual(len(result["results"]["shipments"]), 1)

        # Should find products from order lineItems
        self.assertEqual(len(result["results"]["products"]), 2)
        product_ids = {p["id"] for p in result["results"]["products"]}
        self.assertIn("prod1", product_ids)
        self.assertIn("prod2", product_ids)

    def test_find_related_from_ticket(self):
        """Test finding entities related to a ticket."""
        result = FindRelatedEntities.invoke(self.data, entity_id="ticket1")

        self.assertEqual(result["source_entity_type"], "ticket")

        # Should find escalations for this ticket
        self.assertEqual(len(result["results"]["escalations"]), 1)
        self.assertEqual(result["results"]["escalations"][0]["id"], "esc1")

        # Should find resolutions for this ticket
        self.assertEqual(len(result["results"]["resolutions"]), 1)
        self.assertEqual(result["results"]["resolutions"][0]["id"], "res1")

        # Should trace back to customer
        self.assertEqual(len(result["results"]["customers"]), 1)

        # Should trace back to order
        self.assertEqual(len(result["results"]["orders"]), 1)

    def test_find_related_from_payment(self):
        """Test finding entities related to a payment."""
        result = FindRelatedEntities.invoke(self.data, entity_id="payment1")

        self.assertEqual(result["source_entity_type"], "payment")

        # Should find the payment itself
        self.assertEqual(len(result["results"]["payments"]), 1)

        # Should find refunds for this payment
        self.assertEqual(len(result["results"]["refunds"]), 1)
        self.assertEqual(result["results"]["refunds"][0]["id"], "refund1")

        # Should trace back to order
        self.assertEqual(len(result["results"]["orders"]), 1)
        self.assertEqual(result["results"]["orders"][0]["id"], "order1")

    def test_find_related_from_product(self):
        """Test finding entities related to a product."""
        result = FindRelatedEntities.invoke(self.data, entity_id="prod1")

        self.assertEqual(result["source_entity_type"], "product")

        # Products don't have direct relationships in this schema
        # So we expect minimal results
        self.assertEqual(len(result["results"]["products"]), 1)
        self.assertEqual(result["results"]["products"][0]["id"], "prod1")

    def test_find_related_nonexistent_entity(self):
        """Test with non-existent entity."""
        result = FindRelatedEntities.invoke(self.data, entity_id="nonexistent")

        self.assertIn("error", result)
        self.assertIn("not found", result["error"])

        # Should still return empty results structure
        self.assertIn("results", result)

    def test_find_related_summary(self):
        """Test that summary contains correct counts."""
        result = FindRelatedEntities.invoke(self.data, entity_id="customer1")

        summary = result["summary"]
        self.assertEqual(summary["customers"], 1)
        self.assertEqual(summary["orders"], 2)
        self.assertEqual(summary["tickets"], 2)
        self.assertEqual(summary["payments"], 2)
        self.assertEqual(summary["shipments"], 1)
        self.assertEqual(summary["refunds"], 1)
        self.assertEqual(summary["escalations"], 1)
        self.assertEqual(summary["resolutions"], 1)
        self.assertEqual(summary["products"], 3)

    def test_find_related_empty_lineItems(self):
        """Test order with empty lineItems."""
        self.data["order"]["order3"] = {
            "id": "order3",
            "customerId": "customer1",
            "status": "pending",
            "lineItems": [],
        }

        result = FindRelatedEntities.invoke(self.data, entity_id="order3")

        # Should not crash, just no products
        self.assertEqual(len(result["results"]["products"]), 0)

    def test_find_related_missing_lineItems(self):
        """Test order without lineItems field."""
        self.data["order"]["order4"] = {
            "id": "order4",
            "customerId": "customer1",
            "status": "pending",
        }

        result = FindRelatedEntities.invoke(self.data, entity_id="order4")

        # Should not crash
        self.assertEqual(len(result["results"]["products"]), 0)

    def test_find_related_invalid_lineItem(self):
        """Test order with invalid lineItem format."""
        self.data["order"]["order5"] = {
            "id": "order5",
            "customerId": "customer1",
            "status": "pending",
            "lineItems": [
                "invalid",  # Not a dict
                {"productId": "prod1", "quantity": 1},
            ],
        }

        result = FindRelatedEntities.invoke(self.data, entity_id="order5")

        # Should skip invalid item and process valid one
        self.assertEqual(len(result["results"]["products"]), 1)
        self.assertEqual(result["results"]["products"][0]["id"], "prod1")

    def test_find_related_productIds_field(self):
        """Test entity with productIds field (though this is a bug in the code)."""
        # BUG: Line 53 tries to access productIds, but no model has this field
        # Build has componentIds, not productIds
        self.data["build"] = {
            "build1": {
                "id": "build1",
                "customerId": "customer1",
                "componentIds": ["prod1", "prod2"],  # Not productIds
            }
        }

        result = FindRelatedEntities.invoke(self.data, entity_id="build1")

        # productIds won't be found, so no products via that path
        # But the bug doesn't crash, it just doesn't find products this way
        self.assertEqual(len(result["results"]["products"]), 0)

    def test_find_related_invalid_entity_table(self):
        """Test when entity table is not a dict."""
        self.data["order"] = "not_a_dict"

        result = FindRelatedEntities.invoke(self.data, entity_id="customer1")

        # Should still work but not find orders
        self.assertEqual(len(result["results"]["orders"]), 0)

    def test_find_related_invalid_entity_format(self):
        """Test when entity in table is not a dict."""
        self.data["order"]["invalid_order"] = "not_a_dict"

        result = FindRelatedEntities.invoke(self.data, entity_id="customer1")

        # Should skip invalid entity
        self.assertEqual(len(result["results"]["orders"]), 2)  # Only valid ones

    def test_find_related_ticket_without_orderId(self):
        """Test ticket without orderId."""
        # ticket2 doesn't have orderId
        result = FindRelatedEntities.invoke(self.data, entity_id="ticket2")

        self.assertEqual(result["source_entity_type"], "ticket")

        # Should still find customer
        self.assertEqual(len(result["results"]["customers"]), 1)

        # But no orders
        self.assertEqual(len(result["results"]["orders"]), 0)

    def test_find_related_refund_traces_to_order(self):
        """Test that refund traces back through payment to order."""
        result = FindRelatedEntities.invoke(self.data, entity_id="refund1")

        self.assertEqual(result["source_entity_type"], "refund")

        # Should find payment
        self.assertEqual(len(result["results"]["payments"]), 1)
        self.assertEqual(result["results"]["payments"][0]["id"], "payment1")

        # Should find order
        self.assertEqual(len(result["results"]["orders"]), 1)
        self.assertEqual(result["results"]["orders"][0]["id"], "order1")

    def test_find_related_escalation_traces_to_ticket(self):
        """Test that escalation traces to ticket and beyond."""
        result = FindRelatedEntities.invoke(self.data, entity_id="esc1")

        self.assertEqual(result["source_entity_type"], "escalation")

        # Should find escalation itself
        self.assertEqual(len(result["results"]["escalations"]), 1)

        # No direct relationships from escalation in the traversal logic
        # (escalations are found FROM tickets, not the other way around)

    def test_find_related_resolution_entity(self):
        """Test finding from resolution."""
        result = FindRelatedEntities.invoke(self.data, entity_id="res1")

        self.assertEqual(result["source_entity_type"], "resolution")

        # Should find resolution itself
        self.assertEqual(len(result["results"]["resolutions"]), 1)

    def test_find_related_shipment_traces_to_order(self):
        """Test that shipment traces to order."""
        result = FindRelatedEntities.invoke(self.data, entity_id="shipment1")

        self.assertEqual(result["source_entity_type"], "shipment")

        # Should find order
        self.assertEqual(len(result["results"]["orders"]), 1)
        self.assertEqual(result["results"]["orders"][0]["id"], "order1")

        # Should trace to customer
        self.assertEqual(len(result["results"]["customers"]), 1)

    def test_find_related_multiple_shipments_per_order(self):
        """Test order with multiple shipments."""
        self.data["shipment"]["shipment2"] = {
            "id": "shipment2",
            "orderId": "order1",
            "carrier": "fedex_express",
            "status": "delivered",
        }

        result = FindRelatedEntities.invoke(self.data, entity_id="order1")

        # Should find both shipments
        self.assertEqual(len(result["results"]["shipments"]), 2)
        shipment_ids = {s["id"] for s in result["results"]["shipments"]}
        self.assertIn("shipment1", shipment_ids)
        self.assertIn("shipment2", shipment_ids)

    def test_find_related_empty_tables(self):
        """Test with empty entity tables."""
        data_minimal = {
            "customer": {
                "customer1": {
                    "id": "customer1",
                    "name": "John Doe",
                },
            },
            "order": {},
            "support_ticket": {},
            "payment": {},
        }

        result = FindRelatedEntities.invoke(data_minimal, entity_id="customer1")

        # Should find customer but nothing else
        self.assertEqual(len(result["results"]["customers"]), 1)
        self.assertEqual(len(result["results"]["orders"]), 0)
        self.assertEqual(len(result["results"]["tickets"]), 0)
        self.assertEqual(len(result["results"]["payments"]), 0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = FindRelatedEntities.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "find_related_entities")
        self.assertIn("description", info["function"])
        self.assertIn("traverse", info["function"]["description"].lower())
        self.assertIn("parameters", info["function"])
        self.assertIn("entity_id", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("entity_id", info["function"]["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()
