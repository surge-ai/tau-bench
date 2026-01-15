"""Utility functions for variation_2 tools."""

from typing import Any, Dict, Optional, Set


# Valid data keys that exist in the data dictionary
VALID_DATA_KEYS: Set[str] = {
    "customer",
    "order",
    "support_ticket",
    "payment",
    "shipment",
    "product",
    "build",
    "employee",
    "refund",
    "escalation",
    "resolution",
    "knowledge_base_article",
    "slack_channel",
    "slack_message",
}

# Aliases for convenience (e.g., "ticket" -> "support_ticket")
ENTITY_TYPE_ALIASES: Dict[str, str] = {
    "ticket": "support_ticket",
}


def get_entity_data_key(entity_type: str) -> Optional[str]:
    """
    Get the data key for an entity type, handling aliases.

    Args:
        entity_type: Entity type name (e.g., "order", "ticket", "support_ticket")

    Returns:
        Data key to use in data dict, or None if unknown entity type

    Examples:
        >>> get_entity_data_key("order")
        'order'
        >>> get_entity_data_key("ticket")
        'support_ticket'
        >>> get_entity_data_key("CUSTOMER")
        'customer'
    """
    entity_type_lower = entity_type.lower()

    # Check if it's an alias
    if entity_type_lower in ENTITY_TYPE_ALIASES:
        return ENTITY_TYPE_ALIASES[entity_type_lower]

    # Check if it's a valid data key
    if entity_type_lower in VALID_DATA_KEYS:
        return entity_type_lower

    return None


def get_entity_table(data: Dict[str, Any], entity_type: str) -> Optional[Dict[str, Any]]:
    """
    Get entity table from data, handling entity type aliases.

    Args:
        data: Data dict containing entity tables
        entity_type: Entity type name

    Returns:
        Entity table dict, or None if not found or invalid type

    Example:
        >>> data = {"order": {...}, "support_ticket": {...}}
        >>> get_entity_table(data, "ticket")  # Using alias
        {...}  # Returns support_ticket table
    """
    data_key = get_entity_data_key(entity_type)
    if not data_key:
        return None

    entity_table = data.get(data_key, {})
    if not isinstance(entity_table, dict):
        return None

    return entity_table


def format_invalid_entity_type_error(entity_type: str) -> Dict[str, Any]:
    """Format a standard invalid entity type error message."""
    return {
        "error": f"Unknown entity type: '{entity_type}'",
        "provided_type": entity_type,
        "valid_types": sorted(VALID_DATA_KEYS),
        "aliases": dict(ENTITY_TYPE_ALIASES),
    }
