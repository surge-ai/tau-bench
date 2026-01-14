import json
from typing import Any, Dict, List

from tau_bench.envs.tool import Tool

from .data_utils import (
    get_entity_by_id,
    parse_json_field,
)


class ValidateBuildCompatibility(Tool):
    @staticmethod
    def invoke(data: Dict[str, Any], product_ids: List[str] = None, **kwargs) -> str:
        # Handle product_ids passed via kwargs
        if product_ids is None:
            product_ids = kwargs.get("product_ids", [])

        if not product_ids:
            raise ValueError("product_ids array is required")

        errors = []
        warnings = []

        # Fetch products
        products = []
        found_ids = set()
        for pid in product_ids:
            product = get_entity_by_id(data, "product", pid)
            if product:
                # Parse JSON fields
                if "specs" in product:
                    product["specs"] = parse_json_field(product.get("specs"))
                products.append(product)
                found_ids.add(pid)

        # Check for missing products
        missing_products = [pid for pid in product_ids if pid not in found_ids]
        if missing_products:
            errors.append(f"Products not found: {', '.join(missing_products)}")
            return json.loads(json.dumps({"is_compatible": False, "errors": errors, "warnings": warnings}))

        # Categorize products and sort by id for deterministic behavior
        def by_id(p: Dict[str, Any]) -> str:
            return p.get("id", "")

        cpus = sorted([p for p in products if p.get("category") == "cpu"], key=by_id)
        motherboards = sorted([p for p in products if p.get("category") == "motherboard"], key=by_id)
        memory = sorted([p for p in products if p.get("category") == "memory"], key=by_id)
        psus = sorted([p for p in products if p.get("category") == "psu"], key=by_id)
        gpus = sorted([p for p in products if p.get("category") == "gpu"], key=by_id)
        cases = sorted([p for p in products if p.get("category") == "case"], key=by_id)
        storage = sorted([p for p in products if p.get("category") == "storage"], key=by_id)
        cooling = sorted([p for p in products if p.get("category") == "cooling"], key=by_id)

        # Check for multiple CPUs or motherboards
        if len(cpus) > 1:
            errors.append(f"Build contains multiple CPUs ({len(cpus)}) - a build only requires one CPU")
        if len(motherboards) > 1:
            errors.append(f"Build contains multiple motherboards ({len(motherboards)}) - a build only requires one motherboard")

        # CPU-Motherboard socket compatibility
        if cpus and motherboards:
            cpu = cpus[0]
            mobo = motherboards[0]
            cpu_specs = cpu.get("specs", {}) or {}
            mobo_specs = mobo.get("specs", {}) or {}
            cpu_socket = cpu_specs.get("cpu", {}).get("socket") if isinstance(cpu_specs, dict) else None
            mobo_socket = mobo_specs.get("motherboard", {}).get("socket") if isinstance(mobo_specs, dict) else None

            if cpu_socket and mobo_socket and cpu_socket != mobo_socket:
                errors.append(f"CPU socket {cpu_socket} incompatible with motherboard socket {mobo_socket}")

        # Motherboard-Case form factor compatibility
        if motherboards and cases:
            mobo = motherboards[0]
            case = cases[0]
            mobo_specs = mobo.get("specs", {}) or {}
            case_specs = case.get("specs", {}) or {}
            mobo_form_factor = mobo_specs.get("motherboard", {}).get("formFactor") if isinstance(mobo_specs, dict) else None
            supported_form_factors = case_specs.get("case", {}).get("supportedFormFactors") if isinstance(case_specs, dict) else None

            if mobo_form_factor and supported_form_factors and isinstance(supported_form_factors, list):
                if mobo_form_factor not in supported_form_factors:
                    errors.append(f"Motherboard form factor {mobo_form_factor} not supported by case (supports: {', '.join(supported_form_factors)})")

        # Memory compatibility
        if memory and motherboards:
            mobo = motherboards[0]
            mobo_specs = mobo.get("specs", {}) or {}
            mobo_mem_type = mobo_specs.get("motherboard", {}).get("memoryType") if isinstance(mobo_specs, dict) else None
            mobo_max_speed = mobo_specs.get("motherboard", {}).get("maxMemoryMhz") if isinstance(mobo_specs, dict) else None

            memory_frequencies = []
            for ram in memory:
                ram_specs = ram.get("specs", {}) or {}
                ram_type = ram_specs.get("memory", {}).get("type") if isinstance(ram_specs, dict) else None
                ram_speed = ram_specs.get("memory", {}).get("speedMhz") if isinstance(ram_specs, dict) else None

                if ram_type and mobo_mem_type and ram_type != mobo_mem_type:
                    errors.append(f"Memory type {ram_type} not supported by motherboard (supports {mobo_mem_type})")

                if ram_speed and isinstance(ram_speed, (int, float)):
                    memory_frequencies.append(ram_speed)

            if memory_frequencies and mobo_max_speed:
                max_ram_speed = max(memory_frequencies)
                min_ram_speed = min(memory_frequencies)

                if max_ram_speed > mobo_max_speed:
                    warnings.append(f"Memory will be downclocked from {max_ram_speed}MHz to motherboard maximum of {mobo_max_speed}MHz")

                if len(memory_frequencies) > 1 and min_ram_speed != max_ram_speed:
                    unique_freqs = sorted(set(memory_frequencies))
                    warnings.append(f"Mismatched memory frequencies detected ({', '.join(str(f) + 'MHz' for f in unique_freqs)}) - all memory will run at slowest speed ({min_ram_speed}MHz)")

        # Memory slots compatibility
        if memory and motherboards:
            mobo = motherboards[0]
            mobo_specs = mobo.get("specs", {}) or {}
            max_memory_slots = mobo_specs.get("motherboard", {}).get("maxMemorySlots") if isinstance(mobo_specs, dict) else None

            if max_memory_slots:
                total_memory_modules = 0
                for ram in memory:
                    ram_specs = ram.get("specs", {}) or {}
                    modules = ram_specs.get("memory", {}).get("modules", 1) if isinstance(ram_specs, dict) else 1
                    total_memory_modules += modules

                if total_memory_modules > max_memory_slots:
                    errors.append(f"Total memory modules ({total_memory_modules}) exceed motherboard slots ({max_memory_slots})")

        # SATA storage compatibility
        if storage and motherboards:
            mobo = motherboards[0]
            mobo_specs = mobo.get("specs", {}) or {}
            sata_ports = mobo_specs.get("motherboard", {}).get("sataPorts") if isinstance(mobo_specs, dict) else None

            if sata_ports is not None:
                sata_devices_count = 0
                for storage_device in storage:
                    storage_specs = storage_device.get("specs", {}) or {}
                    interface_type = storage_specs.get("storage", {}).get("interface") if isinstance(storage_specs, dict) else None
                    if interface_type == "SATA":
                        sata_devices_count += 1

                if sata_devices_count > sata_ports:
                    errors.append(f"SATA storage devices ({sata_devices_count}) exceed motherboard SATA ports ({sata_ports})")

        # GPU-Case clearance check
        if gpus and cases:
            case = cases[0]
            case_specs = case.get("specs", {}) or {}
            max_gpu_length = case_specs.get("case", {}).get("gpuMaxLengthMm") if isinstance(case_specs, dict) else None

            if max_gpu_length:
                for gpu in gpus:
                    gpu_specs = gpu.get("specs", {}) or {}
                    gpu_length = gpu_specs.get("gpu", {}).get("lengthMm") if isinstance(gpu_specs, dict) else None

                    if gpu_length and gpu_length > max_gpu_length:
                        errors.append(f"GPU {gpu['name']} length ({gpu_length}mm) exceeds case maximum ({max_gpu_length}mm)")

        # CPU Cooler-Case clearance check
        if cooling and cases:
            case = cases[0]
            case_specs = case.get("specs", {}) or {}
            max_cooler_height = case_specs.get("case", {}).get("coolerMaxHeightMm") if isinstance(case_specs, dict) else None

            if max_cooler_height:
                for cooler in cooling:
                    cooler_specs = cooler.get("specs", {}) or {}
                    cooler_height = cooler_specs.get("cooling", {}).get("heightMm") if isinstance(cooler_specs, dict) else None

                    if cooler_height and cooler_height > max_cooler_height:
                        errors.append(f"CPU cooler {cooler['name']} height ({cooler_height}mm) exceeds case maximum ({max_cooler_height}mm)")

        # PSU wattage check
        if psus:
            psu = psus[0]
            psu_specs = psu.get("specs", {}) or {}
            psu_wattage = psu_specs.get("psu", {}).get("wattage", 0) if isinstance(psu_specs, dict) else 0

            for cpu in cpus:
                cpu_specs = cpu.get("specs", {}) or {}
                cpu_tdp = cpu_specs.get("cpu", {}).get("tdpWatts", 65) if isinstance(cpu_specs, dict) else 65
                if psu_wattage < cpu_tdp:
                    errors.append(f"PSU wattage ({psu_wattage}W) insufficient for CPU TDP ({cpu_tdp}W)")

            for gpu in gpus:
                gpu_specs = gpu.get("specs", {}) or {}
                gpu_recommended_psu = gpu_specs.get("gpu", {}).get("recommendedPsuWatts", 0) if isinstance(gpu_specs, dict) else 0
                if gpu_recommended_psu > 0 and psu_wattage < gpu_recommended_psu:
                    errors.append(f"PSU wattage ({psu_wattage}W) insufficient for GPU requirements ({gpu_recommended_psu}W recommended)")
        elif cpus or gpus:
            warnings.append("No PSU selected")

        return json.loads(json.dumps({
            "is_compatible": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }))

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "validateBuildCompatibility",
                "description": "Validate PC build compatibility for a list of product IDs. Checks CPU-motherboard socket compatibility, motherboard-case form factor compatibility, memory type and speed compatibility, memory slot count, SATA port count, GPU and cooler clearance, and PSU wattage requirements. Returns is_compatible (boolean), errors (list of incompatibility issues), and warnings (list of potential concerns).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "product_ids": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of product IDs to check for compatibility"
                        }
                    },
                    "required": ["product_ids"]
                }
            }
        }
