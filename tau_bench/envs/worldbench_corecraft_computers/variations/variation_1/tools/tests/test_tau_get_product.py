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

# Import tool_impls first so it uses our utils module
import tool_impls.get_product  # noqa: F401

# Now import the tool module normally
if tools_dir not in sys.path:
    sys.path.insert(0, tools_dir)

from tau_get_product import GetProduct


class TestGetProduct(unittest.TestCase):
    def setUp(self):
        """Set up test data with products."""
        self.data: Dict[str, Any] = {
            "Product": {
                "prod1": {
                    "id": "prod1",
                    "name": "Product 1",
                    "category": "cpu",
                    "brand": "Brand1",
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
                    "warrantyMonths": 12,
                },
                "prod2": {
                    "id": "prod2",
                    "name": "Product 2",
                    "category": "gpu",
                    "brand": "Brand2",
                    "price": 200.0,
                    "sku": "SKU-002",
                    "inventory": json.dumps({
                        "inStock": 5,
                        "backorderable": False
                    }),
                    "specs": json.dumps({
                        "gpu": {
                            "memory": "16GB",
                            "clockSpeed": "1800MHz"
                        }
                    }),
                    "warrantyMonths": 24,
                },
                "prod3": {
                    "id": "prod3",
                    "name": "Product 3",
                    "category": "memory",
                    "brand": "Brand3",
                    "price": 50.0,
                    "sku": "SKU-003",
                    # No inventory field
                    # No specs field
                    "warrantyMonths": 36,
                },
            }
        }

    def test_get_product_basic(self):
        """Test getting an existing product."""
        result = GetProduct.invoke(
            self.data,
            product_id="prod1",
        )
        result_dict = json.loads(result)
        
        self.assertIsNotNone(result_dict)
        self.assertEqual(result_dict["id"], "prod1")
        self.assertEqual(result_dict["name"], "Product 1")
        self.assertEqual(result_dict["category"], "cpu")
        self.assertEqual(result_dict["brand"], "Brand1")
        self.assertEqual(result_dict["price"], 100.0)
        self.assertEqual(result_dict["sku"], "SKU-001")
        self.assertEqual(result_dict["warrantyMonths"], 12)

    def test_get_product_nonexistent(self):
        """Test getting a non-existent product."""
        result = GetProduct.invoke(
            self.data,
            product_id="nonexistent",
        )
        result_dict = json.loads(result)
        
        # Should return None (serialized as null in JSON)
        self.assertIsNone(result_dict)

    def test_get_product_parses_inventory_json(self):
        """Test that inventory JSON field is parsed."""
        result = GetProduct.invoke(
            self.data,
            product_id="prod1",
        )
        result_dict = json.loads(result)
        
        # inventory should be parsed from JSON string to dict
        self.assertIn("inventory", result_dict)
        self.assertIsInstance(result_dict["inventory"], dict)
        self.assertEqual(result_dict["inventory"]["inStock"], 10)
        self.assertTrue(result_dict["inventory"]["backorderable"])

    def test_get_product_parses_specs_json(self):
        """Test that specs JSON field is parsed."""
        result = GetProduct.invoke(
            self.data,
            product_id="prod1",
        )
        result_dict = json.loads(result)
        
        # specs should be parsed from JSON string to dict
        self.assertIn("specs", result_dict)
        self.assertIsInstance(result_dict["specs"], dict)
        self.assertIn("cpu", result_dict["specs"])
        self.assertEqual(result_dict["specs"]["cpu"]["socket"], "AM4")

    def test_get_product_missing_inventory_field(self):
        """Test product without inventory field."""
        result = GetProduct.invoke(
            self.data,
            product_id="prod3",
        )
        result_dict = json.loads(result)
        
        # Should still return the product
        self.assertIsNotNone(result_dict)
        self.assertEqual(result_dict["id"], "prod3")
        # inventory field may or may not be present
        if "inventory" in result_dict:
            # If present, should be a dict (parsed) or None
            self.assertIsInstance(result_dict.get("inventory"), (dict, type(None)))

    def test_get_product_missing_specs_field(self):
        """Test product without specs field."""
        result = GetProduct.invoke(
            self.data,
            product_id="prod3",
        )
        result_dict = json.loads(result)
        
        # Should still return the product
        self.assertIsNotNone(result_dict)
        self.assertEqual(result_dict["id"], "prod3")
        # specs field may or may not be present
        if "specs" in result_dict:
            # If present, should be a dict (parsed) or None
            self.assertIsInstance(result_dict.get("specs"), (dict, type(None)))

    def test_get_product_all_fields(self):
        """Test product with all fields populated."""
        result = GetProduct.invoke(
            self.data,
            product_id="prod2",
        )
        result_dict = json.loads(result)
        
        # Check all fields
        self.assertEqual(result_dict["id"], "prod2")
        self.assertEqual(result_dict["name"], "Product 2")
        self.assertEqual(result_dict["category"], "gpu")
        self.assertEqual(result_dict["brand"], "Brand2")
        self.assertEqual(result_dict["price"], 200.0)
        self.assertEqual(result_dict["sku"], "SKU-002")
        self.assertEqual(result_dict["warrantyMonths"], 24)
        
        # Check parsed JSON fields
        self.assertIsInstance(result_dict["inventory"], dict)
        self.assertEqual(result_dict["inventory"]["inStock"], 5)
        self.assertFalse(result_dict["inventory"]["backorderable"])
        
        self.assertIsInstance(result_dict["specs"], dict)
        self.assertIn("gpu", result_dict["specs"])
        self.assertEqual(result_dict["specs"]["gpu"]["memory"], "16GB")

    def test_get_product_invalid_json_handling(self):
        """Test that invalid JSON in fields is handled gracefully."""
        data_invalid_json = {
            "Product": {
                "prod_invalid": {
                    "id": "prod_invalid",
                    "name": "Invalid JSON Product",
                    "inventory": "not valid json {",
                    "specs": "also invalid {",
                }
            }
        }
        
        result = GetProduct.invoke(
            data_invalid_json,
            product_id="prod_invalid",
        )
        result_dict = json.loads(result)
        
        # Should still return the product, with invalid JSON as strings
        self.assertIsNotNone(result_dict)
        self.assertEqual(result_dict["id"], "prod_invalid")
        # Invalid JSON should remain as strings
        self.assertIsInstance(result_dict.get("inventory"), str)
        self.assertIsInstance(result_dict.get("specs"), str)

    def test_get_product_missing_product_id(self):
        """Test that missing product_id raises an error."""
        with self.assertRaises(ValueError):
            GetProduct.invoke(
                self.data,
                product_id="",
            )

    def test_get_product_empty_product_id(self):
        """Test that empty product_id raises an error."""
        with self.assertRaises(ValueError):
            GetProduct.invoke(
                self.data,
                product_id=None,
            )

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = GetProduct.get_info()
        
        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "getProduct")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("product_id", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        self.assertIn("product_id", info["function"]["parameters"]["required"])


if __name__ == "__main__":
    unittest.main()

