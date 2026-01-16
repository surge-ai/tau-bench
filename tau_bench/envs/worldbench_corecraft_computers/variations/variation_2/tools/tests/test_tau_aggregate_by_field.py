import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

from tau_aggregate_by_field import AggregateByField


class TestAggregateByField(unittest.TestCase):
    def setUp(self):
        """Set up test data with various entities."""
        self.data: Dict[str, Any] = {
            "order": {
                "order1": {
                    "id": "order1",
                    "customerId": "customer1",
                    "status": "paid",
                    "total": 150.0,
                },
                "order2": {
                    "id": "order2",
                    "customerId": "customer2",
                    "status": "pending",
                    "total": 200.0,
                },
                "order3": {
                    "id": "order3",
                    "customerId": "customer1",
                    "status": "paid",
                    "total": 300.0,
                },
                "order4": {
                    "id": "order4",
                    "customerId": "customer3",
                    "status": "cancelled",
                    "total": 100.0,
                },
            },
            "support_ticket": {
                "ticket1": {
                    "id": "ticket1",
                    "customerId": "customer1",
                    "priority": "high",
                    "status": "open",
                },
                "ticket2": {
                    "id": "ticket2",
                    "customerId": "customer2",
                    "priority": "normal",
                    "status": "resolved",
                },
                "ticket3": {
                    "id": "ticket3",
                    "customerId": "customer1",
                    "priority": "high",
                    "status": "open",
                },
                "ticket4": {
                    "id": "ticket4",
                    "customerId": "customer3",
                    "priority": "low",
                    "status": "closed",
                },
            },
            "payment": {
                "payment1": {
                    "id": "payment1",
                    "orderId": "order1",
                    "amount": 150.0,
                    "status": "captured",
                },
                "payment2": {
                    "id": "payment2",
                    "orderId": "order2",
                    "amount": 200.0,
                    "status": "pending",
                },
                "payment3": {
                    "id": "payment3",
                    "orderId": "order3",
                    "amount": 300.0,
                    "status": "captured",
                },
            },
            "customer": {
                "customer1": {
                    "id": "customer1",
                    "name": "John Doe",
                    "loyaltyTier": "gold",
                },
                "customer2": {
                    "id": "customer2",
                    "name": "Jane Smith",
                    "loyaltyTier": "silver",
                },
                "customer3": {
                    "id": "customer3",
                    "name": "Bob Johnson",
                    "loyaltyTier": "gold",
                },
            },
        }

    def test_aggregate_by_status(self):
        """Test grouping orders by status."""
        result = AggregateByField.invoke(
            self.data,
            entity_type="order",
            group_by_field="status",
        )

        self.assertIn("aggregations", result)
        self.assertIn("paid", result["aggregations"])
        self.assertIn("pending", result["aggregations"])
        self.assertIn("cancelled", result["aggregations"])

        # Check counts
        self.assertEqual(result["aggregations"]["paid"]["count"], 2)
        self.assertEqual(result["aggregations"]["pending"]["count"], 1)
        self.assertEqual(result["aggregations"]["cancelled"]["count"], 1)

        # Check totals
        self.assertEqual(result["total_entities"], 4)
        self.assertEqual(result["unique_groups"], 3)

    def test_aggregate_with_numeric_field(self):
        """Test grouping orders by status with sum of total field."""
        result = AggregateByField.invoke(
            self.data,
            entity_type="order",
            group_by_field="status",
            count_field="total",
        )

        self.assertIn("aggregations", result)
        paid_agg = result["aggregations"]["paid"]

        # Check that numeric aggregations are present
        self.assertIn("sum", paid_agg)
        self.assertIn("average", paid_agg)
        self.assertIn("min", paid_agg)
        self.assertIn("max", paid_agg)

        # Check values for paid orders (150 + 300 = 450)
        self.assertEqual(paid_agg["sum"], 450.0)
        self.assertEqual(paid_agg["average"], 225.0)
        self.assertEqual(paid_agg["min"], 150.0)
        self.assertEqual(paid_agg["max"], 300.0)

    def test_aggregate_by_priority(self):
        """Test grouping tickets by priority."""
        result = AggregateByField.invoke(
            self.data,
            entity_type="ticket",
            group_by_field="priority",
        )

        self.assertIn("aggregations", result)
        self.assertIn("high", result["aggregations"])
        self.assertIn("normal", result["aggregations"])
        self.assertIn("low", result["aggregations"])

        # Check counts
        self.assertEqual(result["aggregations"]["high"]["count"], 2)
        self.assertEqual(result["aggregations"]["normal"]["count"], 1)
        self.assertEqual(result["aggregations"]["low"]["count"], 1)

    def test_aggregate_by_loyalty_tier(self):
        """Test grouping customers by loyalty tier."""
        result = AggregateByField.invoke(
            self.data,
            entity_type="customer",
            group_by_field="loyaltyTier",
        )

        self.assertIn("aggregations", result)
        self.assertIn("gold", result["aggregations"])
        self.assertIn("silver", result["aggregations"])

        # Check counts
        self.assertEqual(result["aggregations"]["gold"]["count"], 2)
        self.assertEqual(result["aggregations"]["silver"]["count"], 1)

    def test_aggregate_payment_amounts(self):
        """Test grouping payments by status with amount aggregation."""
        result = AggregateByField.invoke(
            self.data,
            entity_type="payment",
            group_by_field="status",
            count_field="amount",
        )

        self.assertIn("aggregations", result)
        captured_agg = result["aggregations"]["captured"]

        # Check captured payments (150 + 300 = 450)
        self.assertEqual(captured_agg["count"], 2)
        self.assertEqual(captured_agg["sum"], 450.0)
        self.assertEqual(captured_agg["average"], 225.0)

    def test_aggregate_unknown_entity_type(self):
        """Test that unknown entity type returns error."""
        result = AggregateByField.invoke(
            self.data,
            entity_type="invalid_type",
            group_by_field="status",
        )

        self.assertIn("error", result)

    def test_aggregate_missing_field(self):
        """Test grouping by a field that doesn't exist on some entities."""
        result = AggregateByField.invoke(
            self.data,
            entity_type="order",
            group_by_field="nonexistent_field",
        )

        # Should group everything under "null"
        self.assertIn("aggregations", result)
        self.assertIn("null", result["aggregations"])
        self.assertEqual(result["aggregations"]["null"]["count"], 4)

    def test_aggregate_with_null_values(self):
        """Test handling of entities with null/missing group field."""
        data_with_nulls = {
            "order": {
                "order1": {"id": "order1", "status": "paid"},
                "order2": {"id": "order2"},  # No status field
                "order3": {"id": "order3", "status": "paid"},
            }
        }

        result = AggregateByField.invoke(
            data_with_nulls,
            entity_type="order",
            group_by_field="status",
        )

        self.assertIn("paid", result["aggregations"])
        self.assertIn("null", result["aggregations"])
        self.assertEqual(result["aggregations"]["paid"]["count"], 2)
        self.assertEqual(result["aggregations"]["null"]["count"], 1)

    def test_aggregate_numeric_field_with_invalid_values(self):
        """Test that non-numeric values are skipped when aggregating."""
        data_with_invalid = {
            "order": {
                "order1": {"id": "order1", "status": "paid", "total": 100.0},
                "order2": {"id": "order2", "status": "paid", "total": "invalid"},
                "order3": {"id": "order3", "status": "paid", "total": 200.0},
            }
        }

        result = AggregateByField.invoke(
            data_with_invalid,
            entity_type="order",
            group_by_field="status",
            count_field="total",
        )

        paid_agg = result["aggregations"]["paid"]
        # Should only sum valid numeric values (100 + 200 = 300)
        self.assertEqual(paid_agg["sum"], 300.0)
        self.assertEqual(paid_agg["average"], 150.0)

    def test_aggregate_empty_entity_table(self):
        """Test aggregation on empty entity table."""
        empty_data = {"order": {}}

        result = AggregateByField.invoke(
            empty_data,
            entity_type="order",
            group_by_field="status",
        )

        self.assertEqual(result["aggregations"], {})
        self.assertEqual(result["total_entities"], 0)
        self.assertEqual(result["unique_groups"], 0)

    def test_aggregate_non_dict_entity_table(self):
        """Test handling when entity table is not a dict."""
        invalid_data = {"order": "not_a_dict"}

        result = AggregateByField.invoke(
            invalid_data,
            entity_type="order",
            group_by_field="status",
        )

        self.assertEqual(result["aggregations"], {})
        self.assertEqual(result["total"], 0)

    def test_aggregate_entity_type_alias(self):
        """Test that entity type aliases work (e.g., 'ticket' -> 'support_ticket')."""
        result = AggregateByField.invoke(
            self.data,
            entity_type="ticket",  # Using alias
            group_by_field="priority",
        )

        self.assertIn("aggregations", result)
        self.assertEqual(result["entity_type"], "ticket")
        self.assertEqual(result["total_entities"], 4)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = AggregateByField.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "aggregate_by_field")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("entity_type", info["function"]["parameters"]["properties"])
        self.assertIn("group_by_field", info["function"]["parameters"]["properties"])
        self.assertIn("count_field", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])


if __name__ == "__main__":
    unittest.main()
