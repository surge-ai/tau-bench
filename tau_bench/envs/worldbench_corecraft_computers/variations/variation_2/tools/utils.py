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

# Valid entity type values for enum (includes both data keys and aliases)
VALID_ENTITY_TYPES: list = sorted(list(VALID_DATA_KEYS) + list(ENTITY_TYPE_ALIASES.keys()))


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


def validate_enum_value(value: str, allowed_values: list, param_name: str) -> Optional[str]:
    """
    Validate that a value is in the allowed enum values.

    Args:
        value: The value to validate
        allowed_values: List of allowed values
        param_name: Name of the parameter (for error messages)

    Returns:
        None if valid, error message string if invalid

    Example:
        >>> error = validate_enum_value("open", ["open", "closed"], "status")
        >>> error is None
        True
        >>> error = validate_enum_value("invalid", ["open", "closed"], "status")
        >>> "invalid" in error
        True
    """
    if value not in allowed_values:
        return f"Invalid {param_name}: '{value}'. Allowed values: {', '.join(allowed_values)}"
    return None


def format_invalid_entity_type_error(entity_type: str) -> Dict[str, Any]:
    """Format a standard invalid entity type error message."""
    return {
        "error": f"Unknown entity type: '{entity_type}'",
        "provided_type": entity_type,
        "valid_types": sorted(VALID_DATA_KEYS),
        "aliases": dict(ENTITY_TYPE_ALIASES),
    }
