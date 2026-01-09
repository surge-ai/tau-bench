import json
import unittest
from typing import Dict, Any

from tau_bench.envs.worldbench_corecraft_computers.variations.variation_1.tools.tau_validate_build_compatibility import ValidateBuildCompatibility


class TestValidateBuildCompatibility(unittest.TestCase):
    def setUp(self):
        """Set up test data with products."""
        self.data: Dict[str, Any] = {
            "product": {
                "cpu1": {
                    "id": "cpu1",
                    "name": "CPU AM4",
                    "category": "cpu",
                    "specs": json.dumps({
                        "cpu": {
                            "socket": "AM4",
                            "cores": 8,
                            "tdpWatts": 65
                        }
                    }),
                },
                "cpu2": {
                    "id": "cpu2",
                    "name": "CPU LGA1700",
                    "category": "cpu",
                    "specs": json.dumps({
                        "cpu": {
                            "socket": "LGA1700",
                            "cores": 12,
                            "tdpWatts": 125
                        }
                    }),
                },
                "mobo1": {
                    "id": "mobo1",
                    "name": "Motherboard AM4",
                    "category": "motherboard",
                    "specs": json.dumps({
                        "motherboard": {
                            "socket": "AM4",
                            "formFactor": "ATX",
                            "memoryType": "DDR4",
                            "maxMemoryMhz": 3200,
                            "maxMemorySlots": 4,
                            "sataPorts": 6
                        }
                    }),
                },
                "mobo2": {
                    "id": "mobo2",
                    "name": "Motherboard LGA1700",
                    "category": "motherboard",
                    "specs": json.dumps({
                        "motherboard": {
                            "socket": "LGA1700",
                            "formFactor": "mATX",
                            "memoryType": "DDR5",
                            "maxMemoryMhz": 5600,
                            "maxMemorySlots": 2,
                            "sataPorts": 4
                        }
                    }),
                },
                "ram1": {
                    "id": "ram1",
                    "name": "RAM DDR4",
                    "category": "memory",
                    "specs": json.dumps({
                        "memory": {
                            "type": "DDR4",
                            "speedMhz": 3200,
                            "modules": 2
                        }
                    }),
                },
                "ram2": {
                    "id": "ram2",
                    "name": "RAM DDR5",
                    "category": "memory",
                    "specs": json.dumps({
                        "memory": {
                            "type": "DDR5",
                            "speedMhz": 5600,
                            "modules": 2
                        }
                    }),
                },
                "gpu1": {
                    "id": "gpu1",
                    "name": "GPU Standard",
                    "category": "gpu",
                    "specs": json.dumps({
                        "gpu": {
                            "lengthMm": 250,
                            "recommendedPsuWatts": 500
                        }
                    }),
                },
                "gpu2": {
                    "id": "gpu2",
                    "name": "GPU Long",
                    "category": "gpu",
                    "specs": json.dumps({
                        "gpu": {
                            "lengthMm": 350,
                            "recommendedPsuWatts": 750
                        }
                    }),
                },
                "case1": {
                    "id": "case1",
                    "name": "Case ATX",
                    "category": "case",
                    "specs": json.dumps({
                        "case": {
                            "supportedFormFactors": ["ATX", "mATX", "ITX"],
                            "gpuMaxLengthMm": 300,
                            "coolerMaxHeightMm": 165
                        }
                    }),
                },
                "case2": {
                    "id": "case2",
                    "name": "Case Small",
                    "category": "case",
                    "specs": json.dumps({
                        "case": {
                            "supportedFormFactors": ["mATX", "ITX"],
                            "gpuMaxLengthMm": 250,
                            "coolerMaxHeightMm": 150
                        }
                    }),
                },
                "psu1": {
                    "id": "psu1",
                    "name": "PSU 600W",
                    "category": "psu",
                    "specs": json.dumps({
                        "psu": {
                            "wattage": 600
                        }
                    }),
                },
                "psu2": {
                    "id": "psu2",
                    "name": "PSU 800W",
                    "category": "psu",
                    "specs": json.dumps({
                        "psu": {
                            "wattage": 800
                        }
                    }),
                },
                "cooler1": {
                    "id": "cooler1",
                    "name": "Cooler Standard",
                    "category": "cooling",
                    "specs": json.dumps({
                        "cooling": {
                            "heightMm": 160
                        }
                    }),
                },
                "cooler2": {
                    "id": "cooler2",
                    "name": "Cooler Tall",
                    "category": "cooling",
                    "specs": json.dumps({
                        "cooling": {
                            "heightMm": 170
                        }
                    }),
                },
            }
        }

    def test_validate_build_compatibility_compatible_build(self):
        """Test validating a compatible build."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo1", "ram1", "psu1"],
        )
        result_dict = json.loads(result)

        # Should be compatible
        self.assertTrue(result_dict["is_compatible"])
        self.assertEqual(len(result_dict["errors"]), 0)

    def test_validate_build_compatibility_socket_mismatch(self):
        """Test validating build with socket mismatch."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo2"],  # AM4 CPU with LGA1700 motherboard
        )
        result_dict = json.loads(result)

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have socket mismatch error
        error_messages = " ".join(result_dict["errors"])
        self.assertIn("socket", error_messages.lower())

    def test_validate_build_compatibility_multiple_cpus(self):
        """Test validating build with multiple CPUs."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "cpu2", "mobo1"],
        )
        result_dict = json.loads(result)

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have multiple CPUs error
        error_messages = " ".join(result_dict["errors"]).lower()
        self.assertTrue("cpu" in error_messages and "multiple" in error_messages)

    def test_validate_build_compatibility_multiple_motherboards(self):
        """Test validating build with multiple motherboards."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo1", "mobo2"],
        )
        result_dict = json.loads(result)

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have multiple motherboards error
        error_messages = " ".join(result_dict["errors"]).lower()
        self.assertTrue("motherboard" in error_messages and "multiple" in error_messages)

    def test_validate_build_compatibility_memory_type_mismatch(self):
        """Test validating build with memory type mismatch."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo1", "ram2"],  # DDR4 motherboard with DDR5 RAM
        )
        result_dict = json.loads(result)

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have memory type mismatch error
        error_messages = " ".join(result_dict["errors"]).lower()
        self.assertIn("memory", error_messages)

    def test_validate_build_compatibility_gpu_length_exceeded(self):
        """Test validating build with GPU too long for case."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo1", "gpu2", "case2"],  # GPU 350mm in case with 250mm max
        )
        result_dict = json.loads(result)

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have GPU length error
        error_messages = " ".join(result_dict["errors"]).lower()
        self.assertIn("length", error_messages)

    def test_validate_build_compatibility_cooler_height_exceeded(self):
        """Test validating build with cooler too tall for case."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo1", "cooler2", "case2"],  # Cooler 170mm in case with 150mm max
        )
        result_dict = json.loads(result)

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have cooler height error
        error_messages = " ".join(result_dict["errors"]).lower()
        self.assertIn("height", error_messages)

    def test_validate_build_compatibility_psu_insufficient_gpu(self):
        """Test validating build with PSU insufficient for GPU."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo1", "gpu2", "psu1"],  # GPU needs 750W, PSU only 600W
        )
        result_dict = json.loads(result)

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have PSU wattage error
        error_messages = " ".join(result_dict["errors"])
        self.assertIn("PSU", error_messages)

    def test_validate_build_compatibility_missing_products(self):
        """Test validating build with missing products."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["nonexistent1", "nonexistent2"],
        )
        result_dict = json.loads(result)

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have missing products error
        error_messages = " ".join(result_dict["errors"]).lower()
        self.assertIn("not found", error_messages)

    def test_validate_build_compatibility_empty_product_ids(self):
        """Test validating build with empty product_ids."""
        with self.assertRaises(ValueError):
            ValidateBuildCompatibility.invoke(
                self.data,
                product_ids=[],
            )

    def test_validate_build_compatibility_result_structure(self):
        """Test that result has correct structure."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo1", "ram1"],
        )
        result_dict = json.loads(result)

        # Should have required fields
        self.assertIn("is_compatible", result_dict)
        self.assertIn("errors", result_dict)
        self.assertIn("warnings", result_dict)

        # Types should be correct
        self.assertIsInstance(result_dict["is_compatible"], bool)
        self.assertIsInstance(result_dict["errors"], list)
        self.assertIsInstance(result_dict["warnings"], list)

    def test_get_info(self):
        """Test that get_info returns the correct structure."""
        info = ValidateBuildCompatibility.get_info()

        self.assertEqual(info["type"], "function")
        self.assertEqual(info["function"]["name"], "validateBuildCompatibility")
        self.assertIn("description", info["function"])
        self.assertIn("parameters", info["function"])
        self.assertIn("product_ids", info["function"]["parameters"]["properties"])
        self.assertIn("required", info["function"]["parameters"])
        required = info["function"]["parameters"]["required"]
        self.assertIn("product_ids", required)


if __name__ == "__main__":
    unittest.main()
