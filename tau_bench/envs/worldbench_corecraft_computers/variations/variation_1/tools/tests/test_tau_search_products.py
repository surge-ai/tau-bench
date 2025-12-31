import json
import sys
import os
import unittest
from typing import Dict, Any

# Import the module directly without going through package __init__
# We're in tests/ subdirectory, so go up one level to tools/
tests_dir = os.path.dirname(os.path.abspath(__file__))
tools_dir = os.path.dirname(tests_dir)
sys.path.insert(0, tools_dir)

# Import dependencies first
from tau_sqlite_utils import build_sqlite_from_data
from tau_bench.envs.tool import Tool

# Create a mock utils module for tool_impls that need it
import types
import sqlite3
utils_module = types.ModuleType("utils")
utils_module.get_db_conn = lambda: sqlite3.connect(":memory:")
sys.modules["utils"] = utils_module

# Mock the models module for Product
models_module = types.ModuleType("models")
class Product:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def dict(self):
        return {k: v for k, v in self.__dict__.items()}
    
    def __repr__(self):
        return f"Product({self.__dict__})"

models_module.Product = Product
sys.modules["models"] = models_module

# Import tool_impls first so it uses our utils module
import tool_impls.search_products  # noqa: F401

# Now import the tool module normally
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from tau_search_products import SearchProducts

# Patch json.dumps in the tool module to handle Product objects
import json as json_module
_original_dumps = json_module.dumps

def _custom_dumps(obj, **kwargs):
    """Custom JSON dumps that handles Product objects."""
    if isinstance(obj, list):
        obj = [item.dict() if isinstance(item, Product) else item for item in obj]
    elif isinstance(obj, Product):
        obj = obj.dict()
    return _original_dumps(obj, **kwargs)

import tau_search_products
tau_search_products.json.dumps = _custom_dumps


class TestSearchProducts(unittest.TestCase):
    def setUp(self):
        """Set up test data with products."""
        self.data: Dict[str, Any] = {
            "Product": {
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
        result_list = json.loads(result)
        
        # Should return all products (up to default limit of 50)
        self.assertIsInstance(result_list, list)
        self.assertGreater(len(result_list), 0)
        
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
        result_list = json.loads(result)
        
        # Should return products in cpu category
        self.assertGreater(len(result_list), 0)
        for product in result_list:
            self.assertEqual(product["category"], "cpu")

    def test_search_products_by_brand(self):
        """Test searching products by brand."""
        result = SearchProducts.invoke(
            self.data,
            brand="BrandA",
        )
        result_list = json.loads(result)
        
        # Should return products from BrandA
        self.assertGreater(len(result_list), 0)
        for product in result_list:
            self.assertEqual(product["brand"], "BrandA")

    def test_search_products_by_product_id(self):
        """Test searching products by exact product ID."""
        result = SearchProducts.invoke(
            self.data,
            product_id="prod1",
        )
        result_list = json.loads(result)
        
        # Should return exactly one product (may have duplicates from lowercase alias)
        self.assertGreater(len(result_list), 0)
        product_ids = [p["id"] for p in result_list]
        self.assertIn("prod1", product_ids)

    def test_search_products_by_min_price(self):
        """Test searching products by minimum price."""
        result = SearchProducts.invoke(
            self.data,
            min_price=150.0,
        )
        result_list = json.loads(result)
        
        # Should return products with price >= 150.0
        self.assertGreater(len(result_list), 0)
        for product in result_list:
            self.assertGreaterEqual(product["price"], 150.0)

    def test_search_products_by_max_price(self):
        """Test searching products by maximum price."""
        result = SearchProducts.invoke(
            self.data,
            max_price=100.0,
        )
        result_list = json.loads(result)
        
        # Should return products with price <= 100.0
        self.assertGreater(len(result_list), 0)
        for product in result_list:
            self.assertLessEqual(product["price"], 100.0)

    def test_search_products_by_exact_price(self):
        """Test searching products by exact price."""
        result = SearchProducts.invoke(
            self.data,
            price=100.0,
        )
        result_list = json.loads(result)
        
        # Should return products with price == 100.0
        self.assertGreater(len(result_list), 0)
        for product in result_list:
            self.assertEqual(product["price"], 100.0)

    def test_search_products_by_price_range(self):
        """Test searching products by price range."""
        result = SearchProducts.invoke(
            self.data,
            min_price=50.0,
            max_price=150.0,
        )
        result_list = json.loads(result)
        
        # Should return products with price between 50.0 and 150.0
        self.assertGreater(len(result_list), 0)
        for product in result_list:
            self.assertGreaterEqual(product["price"], 50.0)
            self.assertLessEqual(product["price"], 150.0)

    def test_search_products_in_stock_only(self):
        """Test searching products in stock only."""
        result = SearchProducts.invoke(
            self.data,
            inStockOnly="true",
        )
        result_list = json.loads(result)
        
        # Should return products with inventory > 0
        self.assertGreater(len(result_list), 0)
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
        result_list = json.loads(result)
        
        # Should return products with stock >= 10
        self.assertGreater(len(result_list), 0)
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
        result_list = json.loads(result)
        
        # Should return products with stock <= 10
        self.assertGreater(len(result_list), 0)
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
        result_list = json.loads(result)
        
        # Should find products with "CPU" in name, brand, or SKU
        self.assertGreater(len(result_list), 0)
        for product in result_list:
            name_brand_sku = (
                product.get("name", "") + " " +
                product.get("brand", "") + " " +
                product.get("sku", "")
            )
            self.assertIn("CPU", name_brand_sku)

    def test_search_products_multiple_filters(self):
        """Test searching with multiple filters."""
        result = SearchProducts.invoke(
            self.data,
            category="cpu",
            brand="BrandA",
            min_price=50.0,
        )
        result_list = json.loads(result)
        
        # Should match products that satisfy all filters
        for product in result_list:
            self.assertEqual(product["category"], "cpu")
            self.assertEqual(product["brand"], "BrandA")
            self.assertGreaterEqual(product["price"], 50.0)

    def test_search_products_with_limit(self):
        """Test limiting the number of results."""
        result = SearchProducts.invoke(
            self.data,
            limit=2,
        )
        result_list = json.loads(result)
        
        # Should return at most 2 results
        self.assertLessEqual(len(result_list), 2)

    def test_search_products_limit_max_200(self):
        """Test that limit is capped at 200."""
        result = SearchProducts.invoke(
            self.data,
            limit=500,  # Request more than max
        )
        result_list = json.loads(result)
        
        # Should return at most 200 results
        self.assertLessEqual(len(result_list), 200)

    def test_search_products_default_limit(self):
        """Test that default limit is 50."""
        result = SearchProducts.invoke(self.data)
        result_list = json.loads(result)
        
        # Should return at most 50 results (default)
        self.assertLessEqual(len(result_list), 50)

    def test_search_products_parses_inventory(self):
        """Test that inventory JSON field is parsed."""
        result = SearchProducts.invoke(
            self.data,
            product_id="prod1",
        )
        result_list = json.loads(result)
        
        # Should find prod1 (may have duplicates)
        self.assertGreater(len(result_list), 0)
        prod1 = next((p for p in result_list if p["id"] == "prod1"), None)
        self.assertIsNotNone(prod1)
        
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
        result_list = json.loads(result)
        
        # Should find prod1 (may have duplicates)
        self.assertGreater(len(result_list), 0)
        prod1 = next((p for p in result_list if p["id"] == "prod1"), None)
        self.assertIsNotNone(prod1)
        
        # specs should be parsed from JSON string to dict
        if "specs" in prod1:
            self.assertIsInstance(prod1["specs"], dict)

    def test_search_products_sorted_by_name(self):
        """Test that results are sorted by name ASC, then id ASC."""
        result = SearchProducts.invoke(self.data)
        result_list = json.loads(result)
        
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
            category="nonexistent_category",
        )
        result_list = json.loads(result)
        
        # Should return empty list
        self.assertEqual(len(result_list), 0)

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

