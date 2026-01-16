import json
import unittest
from typing import Dict, Any

from ..tau_validate_build_compatibility import ValidateBuildCompatibility


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
                "case3": {
                    "id": "case3",
                    "name": "Case ITX Only",
                    "category": "case",
                    "specs": json.dumps({
                        "case": {
                            "supportedFormFactors": ["ITX"],
                            "gpuMaxLengthMm": 200,
                            "coolerMaxHeightMm": 130
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
                "storage1": {
                    "id": "storage1",
                    "name": "SSD SATA",
                    "category": "storage",
                    "specs": json.dumps({
                        "storage": {
                            "interface": "SATA"
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
        result_dict = result

        # Should be compatible
        self.assertTrue(result_dict["is_compatible"])
        self.assertEqual(len(result_dict["errors"]), 0)

    def test_validate_build_compatibility_socket_mismatch(self):
        """Test validating build with socket mismatch."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo2"],  # AM4 CPU with LGA1700 motherboard
        )
        result_dict = result

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have socket mismatch error
        error_messages = " ".join(result_dict["errors"])
        self.assertIn("socket", error_messages.lower())
        self.assertIn("incompatible", error_messages.lower())

    def test_validate_build_compatibility_multiple_cpus(self):
        """Test validating build with multiple CPUs."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "cpu2", "mobo1"],
        )
        result_dict = result

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
        result_dict = result

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have multiple motherboards error
        error_messages = " ".join(result_dict["errors"]).lower()
        self.assertTrue("motherboard" in error_messages and "multiple" in error_messages)

    def test_validate_build_compatibility_form_factor_mismatch(self):
        """Test validating build with form factor mismatch."""
        # mobo1 is ATX, case3 only supports ITX
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo1", "case3"],
        )
        result_dict = result

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have form factor mismatch error
        error_messages = " ".join(result_dict["errors"]).lower()
        self.assertIn("form factor", error_messages)
        self.assertIn("not supported", error_messages)

    def test_validate_build_compatibility_memory_type_mismatch(self):
        """Test validating build with memory type mismatch."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo1", "ram2"],  # DDR4 motherboard with DDR5 RAM
        )
        result_dict = result

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have memory type mismatch error
        error_messages = " ".join(result_dict["errors"]).lower()
        self.assertIn("memory", error_messages)

    def test_validate_build_compatibility_memory_speed_warning(self):
        """Test validating build with memory speed downclocking warning."""
        # Create RAM with speed higher than motherboard max
        data_with_fast_ram = {
            "product": {
                "cpu1": self.data["product"]["cpu1"],
                "mobo1": self.data["product"]["mobo1"],
                "ram3": {
                    "id": "ram3",
                    "name": "RAM DDR4 Fast",
                    "category": "memory",
                    "specs": json.dumps({
                        "memory": {
                            "type": "DDR4",
                            "speedMhz": 4000,  # Faster than mobo1 max of 3200
                            "modules": 2
                        }
                    }),
                },
            }
        }

        result = ValidateBuildCompatibility.invoke(
            data_with_fast_ram,
            product_ids=["cpu1", "mobo1", "ram3"],
        )
        result_dict = result

        # Should be compatible but have warnings
        self.assertTrue(result_dict["is_compatible"])
        # Check for downclocking warning
        warning_messages = " ".join(result_dict.get("warnings", []))
        self.assertIn("downclocked", warning_messages.lower())

    def test_validate_build_compatibility_memory_slots_exceeded(self):
        """Test validating build with too many memory modules."""
        # Create multiple RAM kits that exceed motherboard slots
        data_many_ram = {
            "product": {
                "cpu1": self.data["product"]["cpu1"],
                "mobo1": self.data["product"]["mobo1"],
                "ram1": self.data["product"]["ram1"],  # 2 modules
                "ram3": {
                    "id": "ram3",
                    "name": "RAM Kit 3",
                    "category": "memory",
                    "specs": json.dumps({
                        "memory": {
                            "type": "DDR4",
                            "speedMhz": 3200,
                            "modules": 2
                        }
                    }),
                },
                "ram4": {
                    "id": "ram4",
                    "name": "RAM Kit 4",
                    "category": "memory",
                    "specs": json.dumps({
                        "memory": {
                            "type": "DDR4",
                            "speedMhz": 3200,
                            "modules": 2  # Total would be 6 modules, exceeding 4 slots
                        }
                    }),
                },
            }
        }

        result = ValidateBuildCompatibility.invoke(
            data_many_ram,
            product_ids=["cpu1", "mobo1", "ram1", "ram3", "ram4"],  # 6 modules total
        )
        result_dict = result

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        error_messages = " ".join(result_dict["errors"])
        self.assertIn("memory modules", error_messages.lower())
        self.assertIn("exceed", error_messages.lower())

    def test_validate_build_compatibility_gpu_length_exceeded(self):
        """Test validating build with GPU too long for case."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo1", "gpu2", "case2"],  # GPU 350mm in case with 250mm max
        )
        result_dict = result

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have GPU length error
        error_messages = " ".join(result_dict["errors"]).lower()
        self.assertIn("length", error_messages)
        self.assertIn("exceed", error_messages)

    def test_validate_build_compatibility_cooler_height_exceeded(self):
        """Test validating build with cooler too tall for case."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo1", "cooler2", "case2"],  # Cooler 170mm in case with 150mm max
        )
        result_dict = result

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have cooler height error
        error_messages = " ".join(result_dict["errors"]).lower()
        self.assertIn("height", error_messages)
        self.assertIn("exceed", error_messages)

    def test_validate_build_compatibility_psu_insufficient_cpu(self):
        """Test validating build with PSU insufficient for CPU."""
        # Create low wattage PSU
        data_low_psu = {
            "product": {
                "cpu2": self.data["product"]["cpu2"],  # TDP 125W
                "mobo2": self.data["product"]["mobo2"],
                "psu3": {
                    "id": "psu3",
                    "name": "PSU 50W",
                    "category": "psu",
                    "specs": json.dumps({
                        "psu": {
                            "wattage": 50  # Less than cpu2's TDP of 125W
                        }
                    }),
                },
            }
        }

        result = ValidateBuildCompatibility.invoke(
            data_low_psu,
            product_ids=["cpu2", "mobo2", "psu3"],  # CPU needs 125W, PSU only 50W
        )
        result_dict = result

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have PSU wattage error
        error_messages = " ".join(result_dict["errors"])
        self.assertIn("PSU wattage", error_messages)
        self.assertIn("insufficient", error_messages.lower())

    def test_validate_build_compatibility_psu_insufficient_gpu(self):
        """Test validating build with PSU insufficient for GPU."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo1", "gpu2", "psu1"],  # GPU needs 750W, PSU only 600W
        )
        result_dict = result

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have PSU wattage error
        error_messages = " ".join(result_dict["errors"])
        self.assertIn("PSU", error_messages)

    def test_validate_build_compatibility_no_psu_warning(self):
        """Test validating build without PSU (should generate warning)."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo1", "gpu1"],  # No PSU
        )
        result_dict = result

        # Should be compatible (no errors, just warnings)
        self.assertTrue(result_dict["is_compatible"])
        self.assertGreater(len(result_dict.get("warnings", [])), 0)
        # Should have no PSU warning
        warning_messages = " ".join(result_dict["warnings"])
        self.assertIn("PSU", warning_messages)

    def test_validate_build_compatibility_missing_products(self):
        """Test validating build with missing products."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["nonexistent1", "nonexistent2"],
        )
        result_dict = result

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have missing products error
        error_messages = " ".join(result_dict["errors"]).lower()
        self.assertIn("not found", error_messages)

    def test_validate_build_compatibility_empty_product_ids(self):
        """Test validating build with empty product_ids."""
        result = ValidateBuildCompatibility.invoke(
                self.data,
                product_ids=[],
)

        self.assertIn("error", result)

    def test_validate_build_compatibility_sata_ports_exceeded(self):
        """Test validating build with too many SATA devices."""
        # Create multiple SATA storage devices
        data_many_sata = {
            "product": {
                "cpu1": self.data["product"]["cpu1"],
                "mobo1": self.data["product"]["mobo1"],  # Has 6 SATA ports
                "storage1": self.data["product"]["storage1"],
                "storage2": {
                    "id": "storage2",
                    "name": "SSD SATA 2",
                    "category": "storage",
                    "specs": json.dumps({"storage": {"interface": "SATA"}}),
                },
                "storage3": {
                    "id": "storage3",
                    "name": "SSD SATA 3",
                    "category": "storage",
                    "specs": json.dumps({"storage": {"interface": "SATA"}}),
                },
                "storage4": {
                    "id": "storage4",
                    "name": "SSD SATA 4",
                    "category": "storage",
                    "specs": json.dumps({"storage": {"interface": "SATA"}}),
                },
                "storage5": {
                    "id": "storage5",
                    "name": "SSD SATA 5",
                    "category": "storage",
                    "specs": json.dumps({"storage": {"interface": "SATA"}}),
                },
                "storage6": {
                    "id": "storage6",
                    "name": "SSD SATA 6",
                    "category": "storage",
                    "specs": json.dumps({"storage": {"interface": "SATA"}}),
                },
                "storage7": {
                    "id": "storage7",
                    "name": "SSD SATA 7",
                    "category": "storage",
                    "specs": json.dumps({"storage": {"interface": "SATA"}}),
                },
            }
        }

        result = ValidateBuildCompatibility.invoke(
            data_many_sata,
            product_ids=["cpu1", "mobo1", "storage1", "storage2", "storage3", "storage4", "storage5", "storage6", "storage7"],  # 7 SATA devices, mobo1 has 6 ports
        )
        result_dict = result

        # Should not be compatible
        self.assertFalse(result_dict["is_compatible"])
        self.assertGreater(len(result_dict["errors"]), 0)
        # Should have SATA ports error
        error_messages = " ".join(result_dict["errors"])
        self.assertIn("SATA", error_messages)
        self.assertIn("exceed", error_messages.lower())

    def test_validate_build_compatibility_mismatched_memory_frequencies(self):
        """Test validating build with mismatched memory frequencies."""
        # Create RAM with different speeds
        data_mixed_ram = {
            "product": {
                "cpu1": self.data["product"]["cpu1"],
                "mobo1": self.data["product"]["mobo1"],
                "ram1": self.data["product"]["ram1"],  # 3200 MHz
                "ram3": {
                    "id": "ram3",
                    "name": "RAM DDR4 Slow",
                    "category": "memory",
                    "specs": json.dumps({
                        "memory": {
                            "type": "DDR4",
                            "speedMhz": 2400,  # Different speed than ram1 (3200)
                            "modules": 2
                        }
                    }),
                },
            }
        }

        result = ValidateBuildCompatibility.invoke(
            data_mixed_ram,
            product_ids=["cpu1", "mobo1", "ram1", "ram3"],  # Mixed speeds
        )
        result_dict = result

        # Should be compatible but have warning about mismatched frequencies
        self.assertTrue(result_dict["is_compatible"])
        # Check for frequency mismatch warning
        warning_messages = " ".join(result_dict.get("warnings", []))
        self.assertTrue(
            "frequency" in warning_messages.lower() or
            "mismatch" in warning_messages.lower() or
            "mismatched" in warning_messages.lower()
        )

    def test_validate_build_compatibility_result_structure(self):
        """Test that result has correct structure."""
        result = ValidateBuildCompatibility.invoke(
            self.data,
            product_ids=["cpu1", "mobo1", "ram1"],
        )
        result_dict = result

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
