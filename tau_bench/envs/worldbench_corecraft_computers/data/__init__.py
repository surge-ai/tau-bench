# Copyright Sierra

import json
import os
from typing import Any

# Load data from worldbench_corecraft_computers/data/ directory
FOLDER_PATH = os.path.dirname(__file__)
DATA_PATH = FOLDER_PATH


def load_data() -> dict[str, Any]:
    data = {}
    json_files = [
        "build.json",
        "bundle.json",
        "compatibility_rule.json",
        "customer.json",
        "employee.json",
        "escalation.json",
        "knowledge_base_article.json",
        "linkedin_profile.json",
        "order.json",
        "payment.json",
        "product.json",
        "refund.json",
        "resolution.json",
        "shipment.json",
        "slack_channel.json",
        "slack_message.json",
        "support_ticket.json",
    ]
    for json_file in json_files:
        file_path = os.path.join(DATA_PATH, json_file)
        if os.path.exists(file_path):
            with open(file_path) as f:
                key = json_file.replace(".json", "")
                data[key] = json.load(f)
    return data

