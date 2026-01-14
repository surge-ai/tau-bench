# Copyright Sierra

import json
import os
from datetime import datetime
from typing import Any, Optional

# Load data from worldbench_corecraft_computers/data/ directory
FOLDER_PATH = os.path.dirname(__file__)
DATA_PATH = FOLDER_PATH


def _parse_iso_datetime(date_str: str) -> Optional[datetime]:
    """Parse ISO 8601 datetime string to datetime object."""
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _filter_by_created_at(data: dict[str, Any], cutoff_time: datetime) -> dict[str, Any]:
    """
    Filter data to only include entities with createdAt before the cutoff time.
    Entities without createdAt are kept (not filtered out).

    Data structure is: { collection_name: { entity_id: { ...fields incl createdAt... } } }
    """
    filtered_data = {}
    for collection_name, entities in data.items():
        if not isinstance(entities, dict):
            filtered_data[collection_name] = entities
            continue
        filtered_entities = {}
        for entity_id, entity in entities.items():
            if not isinstance(entity, dict):
                filtered_entities[entity_id] = entity
                continue
            if "createdAt" in entity:
                created_at = _parse_iso_datetime(entity["createdAt"])
                if created_at is not None and created_at > cutoff_time:
                    continue  # Skip this entity
            filtered_entities[entity_id] = entity
        filtered_data[collection_name] = filtered_entities
    return filtered_data


def _inject_ids(data: dict[str, Any]) -> dict[str, Any]:
    """
    Inject 'id' field into each entity from the key.
    Data structure is: { collection_name: { entity_id: { ...fields... } } }
    """
    for collection_name, entities in data.items():
        if not isinstance(entities, dict):
            continue
        for entity_id, entity in entities.items():
            if isinstance(entity, dict) and "id" not in entity:
                entity["id"] = entity_id
    return data


def load_data(current_time: Optional[str] = None) -> dict[str, Any]:
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

    # Inject IDs from keys into each entity
    data = _inject_ids(data)

    # Filter data by createdAt if current_time is provided
    if current_time is not None:
        cutoff_time = _parse_iso_datetime(current_time)
        if cutoff_time is not None:
            data = _filter_by_created_at(data, cutoff_time)

    return data

