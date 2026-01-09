import json
import unittest
from typing import Dict, Any

from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tools.tau_search_customers import SearchCustomers


class TestSearchCustomers(unittest.TestCase):
    def setUp(self):
        """Set up test data with customers."""
        self.data: Dict[str, Any] = {
            "customer": {
                "customer1": {
                    "id": "customer1",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "phone": "(555) 123-4567",
                    "loyaltyTier": "gold",
                    "addresses": json.dumps([
                        {
                            "label": "shipping",
                            "line1": "123 Main St",
                            "city": "New York",
                            "region": "NY",
                            "postalCode": "10001",
                            "country": "US"
                        }
                    ]),
                    "createdAt": "2025-09-01T00:00:00Z",
                },
                "customer2": {
                    "id": "customer2",
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "phone": "(555) 987-6543",
                    "loyaltyTier": "silver",
                    "addresses": json.dumps([
                        {
                            "label": "billing",
                            "line1": "456 Oak Ave",
                            "city": "Los Angeles",
                            "region": "CA",
                            "postalCode": "90001",
                            "country": "US"
                        }
                    ]),
                    "createdAt": "2025-09-02T00:00:00Z",
                },
                "customer3": {
                    "id": "customer3",
                    "name": "Bob Johnson",
                    "email": "bob@example.com",
                    "phone": "(555) 111-2222",
                    "loyaltyTier": "platinum",
                    "addresses": json.dumps([
                        {
                            "label": "shipping",
                            "line1": "789 Pine Rd",
                            "city": "Chicago",
                            "region": "IL",
                            "postalCode": "60601",
                            "country": "US"
                        }
                    ]),
                    "createdAt": "2025-09-03T00:00:00Z",
                },
            }
        }

    def test_search_customers_no_filters(self):
        """Test searching customers with no filters."""
        result = SearchCustomers.invoke(self.data)
        result_list = json.loads(result)

        # Should return all customers (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertEqual(len(result_list), 3)

        # Check structure of first customer
        if result_list:
            customer = result_list[0]
            self.assertIn("id", customer)
            self.assertIn("name", customer)
            self.assertIn("email", customer)

    def test_search_customers_by_id(self):
        """Test searching customers by exact ID."""
        result = SearchCustomers.invoke(
            self.data,
            customer_id="customer1",
        )
        result_list = json.loads(result)

        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["id"], "customer1")
        self.assertEqual(result_list[0]["name"], "John Doe")

    def test_search_customers_by_name(self):
        """Test searching customers by name (partial search)."""
        result = SearchCustomers.invoke(
            self.data,
            name="John",
        )
        result_list = json.loads(result)

        # Should find customers with "John" in name
        self.assertGreater(len(result_list), 0)
        for customer in result_list:
            self.assertIn("John", customer["name"])

    def test_search_customers_by_email(self):
        """Test searching customers by exact email."""
        result = SearchCustomers.invoke(
            self.data,
            email="jane@example.com",
        )
        result_list = json.loads(result)

        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["email"], "jane@example.com")

    def test_search_customers_by_phone(self):
        """Test searching customers by exact phone."""
        result = SearchCustomers.invoke(
            self.data,
            phone="(555) 123-4567",
        )
        result_list = json.loads(result)

        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["phone"], "(555) 123-4567")

    def test_search_customers_by_loyalty_tier(self):
        """Test searching customers by loyalty tier."""
        result = SearchCustomers.invoke(
            self.data,
            loyalty_tier="gold",
        )
        result_list = json.loads(result)

        # Should return customers with gold tier
        self.assertGreater(len(result_list), 0)
        for customer in result_list:
            self.assertEqual(customer["loyaltyTier"], "gold")

    def test_search_customers_by_address_text(self):
        """Test searching customers by address text."""
        result = SearchCustomers.invoke(
            self.data,
            address_text="New York",
        )
        result_list = json.loads(result)

        # Should find customers with "New York" in addresses
        self.assertGreater(len(result_list), 0)
        # Addresses should be parsed from JSON
        for customer in result_list:
            if "addresses" in customer:
                addresses_str = json.dumps(customer["addresses"])
                self.assertIn("New York", addresses_str)

    def test_search_customers_filter_created_after(self):
        """Test filtering customers created after a date."""
        result = SearchCustomers.invoke(
            self.data,
            created_after="2025-09-02T00:00:00Z",
        )
        result_list = json.loads(result)

        # Should only include customers created on or after 2025-09-02
        self.assertGreater(len(result_list), 0)
        for customer in result_list:
            self.assertGreaterEqual(customer["createdAt"], "2025-09-02T00:00:00Z")

    def test_search_customers_filter_created_before(self):
        """Test filtering customers created before a date."""
        result = SearchCustomers.invoke(
            self.data,
            created_before="2025-09-02T12:00:00Z",
        )
        result_list = json.loads(result)

        # Should only include customers created before the date
        self.assertGreater(len(result_list), 0)
        self.assertLess(len(result_list), 3)

    def test_search_customers_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchCustomers.invoke(
            self.data,
            name="John",
            loyalty_tier="gold",
        )
        result_list = json.loads(result)

        # Should match customers that satisfy all filters
        for customer in result_list:
            self.assertIn("John", customer["name"])
            self.assertEqual(customer["loyaltyTier"], "gold")

    def test_search_customers_with_limit(self):
        """Test limiting the number of results."""
        result = SearchCustomers.invoke(
            self.data,
            limit=2,
        )
        result_list = json.loads(result)

        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_customers_limit_max_200(self):
        """Test that limit is capped at 200."""
        result = SearchCustomers.invoke(
            self.data,
            limit=500,  # Request more than max
        )
        result_list = json.loads(result)

        # Should return at most 200 results
        self.assertLessEqual(len(result_list), 200)

    def test_search_customers_default_limit(self):
        """Test that default limit is 50."""
        result = SearchCustomers.invoke(self.data)
        result_list = json.loads(result)

        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_customers_parses_addresses(self):
        """Test that addresses JSON field is parsed."""
        result = SearchCustomers.invoke(
            self.data,
            customer_id="customer1",
        )
        result_list = json.loads(result)

        self.assertEqual(len(result_list), 1)
        customer1 = result_list[0]

        # addresses should be parsed from JSON string to list
        self.assertIsInstance(customer1["addresses"], list)
        if customer1["addresses"]:
            self.assertIsInstance(customer1["addresses"][0], dict)

    def test_search_customers_sorted_by_name(self):
        """Test that results are sorted by name ASC, then id ASC."""
        result = SearchCustomers.invoke(self.data)
        result_list = json.loads(result)

        if len(result_list) >= 2:
            # Check that customers are sorted by name
            for i in range(len(result_list) - 1):
                current_name = result_list[i]["name"]
                next_name = result_list[i + 1]["name"]
                # Names should be in ascending order
                if current_name == next_name:
                    # If names are equal, check IDs
                    current_id = result_list[i]["id"]
                    next_id = result_list[i + 1]["id"]
                    self.assertLessEqual(current_id, next_id)
                else:
                    self.assertLessEqual(current_name, next_name)

    def test_search_customers_no_results(self):
        """Test search with filters that match no customers."""
        result = SearchCustomers.invoke(
            self.data,
            customer_id="nonexistent",
        )
        result_list = json.loads(result)

        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchCustomers.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "searchCustomers")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("customer_id", info["function"]["parameters"]["properties"])
        self.assertIn("name", info["function"]["parameters"]["properties"])
        self.assertIn("email", info["function"]["parameters"]["properties"])
        self.assertIn("phone", info["function"]["parameters"]["properties"])
        self.assertIn("loyalty_tier", info["function"]["parameters"]["properties"])
        self.assertIn("address_text", info["function"]["parameters"]["properties"])
        self.assertIn("created_after", info["function"]["parameters"]["properties"])
        self.assertIn("created_before", info["function"]["parameters"]["properties"])
        self.assertIn("limit", info["function"]["parameters"]["properties"])
        # All parameters are optional
        self.assertEqual(info["function"]["parameters"].get("required", []), [])


if __name__ == "__main__":
    unittest.main()
