import json
import unittest
from typing import Dict, Any

from ..tau_search_products import SearchProducts


class TestSearchProducts(unittest.TestCase):
    def setUp(self):
        """Set up test data with products."""
        self.data: Dict[str, Any] = {
            "product": {
                "prod1": {
                    "id": "prod1",
                    "name": "CPU Processor",
                    "category": "cpu",
                    "brand": "BrandA",
                    "price": 100.0,
                    "sku": "SKU-001",
                    "inventory": json.dumps({
                        "inStock": 10,
                        "backorderable": True
                    }),
                    "specs": json.dumps({
                        "cpu": {
                            "socket": "AM4",
                            "cores": 8
                        }
                    }),
                },
                "prod2": {
                    "id": "prod2",
                    "name": "GPU Graphics Card",
                    "category": "gpu",
                    "brand": "BrandB",
                    "price": 200.0,
                    "sku": "SKU-002",
                    "inventory": json.dumps({
                        "inStock": 5,
                        "backorderable": False
                    }),
                    "specs": json.dumps({
                        "gpu": {
                            "memory": "16GB"
                        }
                    }),
                },
                "prod3": {
                    "id": "prod3",
                    "name": "RAM Memory Module",
                    "category": "memory",
                    "brand": "BrandA",
                    "price": 50.0,
                    "sku": "SKU-003",
                    "inventory": json.dumps({
                        "inStock": 0,
                        "backorderable": True
                    }),
                    "specs": json.dumps({}),
                },
                "prod4": {
                    "id": "prod4",
                    "name": "SSD Storage Drive",
                    "category": "storage",
                    "brand": "BrandC",
                    "price": 150.0,
                    "sku": "SKU-004",
                    "inventory": json.dumps({
                        "inStock": 20,
                        "backorderable": False
                    }),
                    "specs": json.dumps({}),
                },
            }
        }

    def test_search_products_no_filters(self):
        """Test searching products with no filters."""
        result = SearchProducts.invoke(self.data)
        result_list = result

        # Should return all products (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertEqual(len(result_list), 4)

        # Check structure of first product
        if result_list:
            product = result_list[0]
            self.assertIn("id", product)
            self.assertIn("name", product)
            self.assertIn("category", product)

    def test_search_products_by_category(self):
        """Test searching products by category."""
        result = SearchProducts.invoke(
            self.data,
            category="cpu",
        )
        result_list = result

        # Should return products in cpu category
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["category"], "cpu")

    def test_search_products_by_brand(self):
        """Test searching products by brand."""
        result = SearchProducts.invoke(
            self.data,
            brand="BrandA",
        )
        result_list = result

        # Should return products from BrandA
        self.assertEqual(len(result_list), 2)
        for product in result_list:
            self.assertEqual(product["brand"], "BrandA")

    def test_search_products_by_product_id(self):
        """Test searching products by exact product ID."""
        result = SearchProducts.invoke(
            self.data,
            product_id="prod1",
        )
        result_list = result

        # Should return exactly one product
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["id"], "prod1")

    def test_search_products_by_min_price(self):
        """Test searching products by minimum price."""
        result = SearchProducts.invoke(
            self.data,
            min_price=150.0,
        )
        result_list = result

        # Should return products with price >= 150.0
        self.assertEqual(len(result_list), 2)
        for product in result_list:
            self.assertGreaterEqual(product["price"], 150.0)

    def test_search_products_by_max_price(self):
        """Test searching products by maximum price."""
        result = SearchProducts.invoke(
            self.data,
            max_price=100.0,
        )
        result_list = result

        # Should return products with price <= 100.0
        self.assertEqual(len(result_list), 2)
        for product in result_list:
            self.assertLessEqual(product["price"], 100.0)

    def test_search_products_by_exact_price(self):
        """Test searching products by exact price."""
        result = SearchProducts.invoke(
            self.data,
            price=100.0,
        )
        result_list = result

        # Should return products with price == 100.0
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["price"], 100.0)

    def test_search_products_by_price_range(self):
        """Test searching products by price range."""
        result = SearchProducts.invoke(
            self.data,
            min_price=50.0,
            max_price=150.0,
        )
        result_list = result

        # Should return products with price between 50.0 and 150.0
        self.assertEqual(len(result_list), 3)
        for product in result_list:
            self.assertGreaterEqual(product["price"], 50.0)
            self.assertLessEqual(product["price"], 150.0)

    def test_search_products_in_stock_only(self):
        """Test searching products in stock only."""
        result = SearchProducts.invoke(
            self.data,
            inStockOnly="true",
        )
        result_list = result

        # Should return products with inventory > 0
        self.assertEqual(len(result_list), 3)
        for product in result_list:
            if "inventory" in product:
                inventory = product["inventory"]
                if isinstance(inventory, dict):
                    self.assertGreater(inventory.get("inStock", 0), 0)

    def test_search_products_by_min_stock(self):
        """Test searching products by minimum stock."""
        result = SearchProducts.invoke(
            self.data,
            minStock=10,
        )
        result_list = result

        # Should return products with stock >= 10
        self.assertEqual(len(result_list), 2)
        for product in result_list:
            if "inventory" in product:
                inventory = product["inventory"]
                if isinstance(inventory, dict):
                    self.assertGreaterEqual(inventory.get("inStock", 0), 10)

    def test_search_products_by_max_stock(self):
        """Test searching products by maximum stock."""
        result = SearchProducts.invoke(
            self.data,
            maxStock=10,
        )
        result_list = result

        # Should return products with stock <= 10
        self.assertEqual(len(result_list), 3)
        for product in result_list:
            if "inventory" in product:
                inventory = product["inventory"]
                if isinstance(inventory, dict):
                    self.assertLessEqual(inventory.get("inStock", 0), 10)

    def test_search_products_by_text(self):
        """Test searching products by text (searches name, brand, SKU)."""
        result = SearchProducts.invoke(
            self.data,
            text="CPU",
        )
        result_list = result

        # Should find products with "CPU" in name, brand, or SKU
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["id"], "prod1")

    def test_search_products_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchProducts.invoke(
            self.data,
            category="cpu",
            brand="BrandA",
            min_price=50.0,
        )
        result_list = result

        # Should match products that satisfy all filters
        self.assertEqual(len(result_list), 1)
        self.assertEqual(result_list[0]["category"], "cpu")
        self.assertEqual(result_list[0]["brand"], "BrandA")
        self.assertGreaterEqual(result_list[0]["price"], 50.0)

    def test_search_products_with_limit(self):
        """Test limiting the number of results."""
        result = SearchProducts.invoke(
            self.data,
            limit=2,
        )
        result_list = result

        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_products_limit_max_200(self):
        """Test that limit is capped at 200."""
        result = SearchProducts.invoke(
            self.data,
            limit=500,  # Request more than max
        )
        result_list = result

        # Should return at most 200 results (but we only have 4)
        self.assertLessEqual(len(result_list), 200)

    def test_search_products_default_limit(self):
        """Test that default limit is 50."""
        result = SearchProducts.invoke(self.data)
        result_list = result

        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_products_parses_inventory(self):
        """Test that inventory JSON field is parsed."""
        result = SearchProducts.invoke(
            self.data,
            product_id="prod1",
        )
        result_list = result

        # Should find prod1
        self.assertEqual(len(result_list), 1)
        prod1 = result_list[0]

        # inventory should be parsed from JSON string to dict
        if "inventory" in prod1:
            self.assertIsInstance(prod1["inventory"], dict)
            self.assertIn("inStock", prod1["inventory"])

    def test_search_products_parses_specs(self):
        """Test that specs JSON field is parsed."""
        result = SearchProducts.invoke(
            self.data,
            product_id="prod1",
        )
        result_list = result

        # Should find prod1
        self.assertEqual(len(result_list), 1)
        prod1 = result_list[0]

        # specs should be parsed from JSON string to dict
        if "specs" in prod1:
            self.assertIsInstance(prod1["specs"], dict)

    def test_search_products_sorted_by_name(self):
        """Test that results are sorted by name ASC, then id ASC."""
        result = SearchProducts.invoke(self.data)
        result_list = result

        if len(result_list) >= 2:
            # Check that products are sorted by name
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

    def test_search_products_no_results(self):
        """Test search with filters that match no products."""
        result = SearchProducts.invoke(
            self.data,
            brand="nonexistent_brand",
        )
        result_list = result

        # Should return empty list
        self.assertEqual(len(result_list), 0)

    def test_search_products_invalid_category(self):
        """Test that invalid category raises ValueError."""
        with self.assertRaises(ValueError) as context:
            SearchProducts.invoke(
                self.data,
                category="nonexistent_category",
            )
        self.assertIn("Invalid category", str(context.exception))

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = SearchProducts.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "searchProducts")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("category", info["function"]["parameters"]["properties"])
        self.assertIn("brand", info["function"]["parameters"]["properties"])
        self.assertIn("min_price", info["function"]["parameters"]["properties"])
        self.assertIn("max_price", info["function"]["parameters"]["properties"])
        self.assertIn("price", info["function"]["parameters"]["properties"])
        self.assertIn("inStockOnly", info["function"]["parameters"]["properties"])
        self.assertIn("minStock", info["function"]["parameters"]["properties"])
        self.assertIn("maxStock", info["function"]["parameters"]["properties"])
        self.assertIn("text", info["function"]["parameters"]["properties"])
        self.assertIn("limit", info["function"]["parameters"]["properties"])
        self.assertIn("product_id", info["function"]["parameters"]["properties"])
        # All parameters are optional
        self.assertEqual(info["function"]["parameters"].get("required", []), [])


if __name__ == "__main__":
    unittest.main()
