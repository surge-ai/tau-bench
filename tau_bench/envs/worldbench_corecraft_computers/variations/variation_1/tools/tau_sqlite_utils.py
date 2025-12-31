# typed: ignore
"""tau_sqlite_utils.py

Shared helpers for Tau-Bench tools that want to keep (legacy) SQL read logic while Tau itself
stores canonical state in the in-memory `data` dict.

Pattern:
  - Tools receive `data: Dict[str, Any]` from the Env
  - We build an in-memory SQLite DB from `data` on each invoke()
  - Read tools can run SQL against that DB
  - Write tools should mutate `data` directly; subsequent reads will see changes because
    the DB is rebuilt from the mutated `data`.
"""

import json
import sqlite3
from typing import Any, Dict, List


def infer_sql_type(v: Any) -> str:
    if isinstance(v, bool) or isinstance(v, int):
        return "INTEGER"
    if isinstance(v, float):
        return "REAL"
    return "TEXT"


def iter_rows(rows: Any) -> List[Dict[str, Any]]:
    """Normalize supported row container shapes into a list of dict rows.
    
    If rows is a dict keyed by IDs, adds the key as an 'id' field to each row.
    """
    if rows is None:
        return []
    if isinstance(rows, list):
        return [r for r in rows if isinstance(r, dict)]
    if isinstance(rows, dict):
        result = []
        for key, value in rows.items():
            if isinstance(value, dict):
                # If the row doesn't already have an 'id' field, add the key as 'id'
                row = value.copy()
                if 'id' not in row:
                    row['id'] = key
                result.append(row)
        return result
    return []


def create_and_insert(conn: sqlite3.Connection, table: str, row_list: List[Dict[str, Any]]) -> None:
    """Create a table and insert rows (best-effort). Nested values are JSON-dumped."""
    if not row_list:
        return

    cols: Dict[str, str] = {}
    for r in row_list:
        for k, v in r.items():
            cols.setdefault(k, infer_sql_type(v))
    if not cols:
        return

    cur = conn.cursor()
    col_defs = ", ".join([f'"{k}" {t}' for k, t in cols.items()])
    # SQLite is case-insensitive for table names, so "Order" and "order" are the same.
    # We use CREATE TABLE IF NOT EXISTS to avoid errors if the table already exists.
    cur.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({col_defs})')

    col_names = list(cols.keys())
    placeholders = ", ".join(["?"] * len(col_names))
    insert_sql = (
        f'INSERT INTO "{table}" ('
        + ", ".join([f'"{c}"' for c in col_names])
        + f') VALUES ({placeholders})'
    )

    for r in row_list:
        values = []
        for c in col_names:
            v = r.get(c)
            if isinstance(v, bool):
                v = int(v)
            elif isinstance(v, (dict, list)):
                v = json.dumps(v)
            values.append(v)
        cur.execute(insert_sql, values)


def _to_sql_table_name(key: str) -> str:
    """Convert data key to SQL table name.
    
    Maps lowercase/snake_case keys to capitalized table names expected by SQL queries.
    Examples:
        "order" -> "Order"
        "payment" -> "Payment"
        "support_ticket" -> "SupportTicket"
        "customer" -> "Customer"
    """
    # Map known keys to their SQL table names (matching what SQL queries expect)
    table_name_map = {
        "order": "Order",
        "payment": "Payment",
        "product": "Product",
        "customer": "Customer",
        "support_ticket": "SupportTicket",
        "shipment": "Shipment",
        "build": "Build",
        "refund": "Refund",
        "resolution": "Resolution",
        "escalation": "Escalation",
        "bundle": "Bundle",
        "compatibility_rule": "CompatibilityRule",
        "employee": "Employee",
        "knowledge_base_article": "KnowledgeBaseArticle",
        "linkedin_profile": "LinkedInProfile",
        "slack_channel": "SlackChannel",
        "slack_message": "SlackMessage",
    }
    
    # Check if we have a mapping
    if key in table_name_map:
        return table_name_map[key]
    
    # Otherwise, capitalize first letter and convert snake_case to CamelCase
    parts = key.split("_")
    return "".join(part.capitalize() for part in parts)


def build_sqlite_from_data(conn: sqlite3.Connection, data: Dict[str, Any], *, add_lowercase_alias: bool = True) -> None:
    """Create one SQLite table per top-level key in `data` and insert its rows.

    Creates tables with:
    1. The original key name (e.g., "order")
    2. The SQL table name (e.g., "Order") - for compatibility with SQL queries
    3. If add_lowercase_alias=True, a lowercase alias if the key differs (e.g., "order" -> "orders")
    """
    conn.row_factory = sqlite3.Row

    for key, rows in data.items():
        row_list = iter_rows(rows)
        if not row_list:
            continue

        # Get the SQL table name that queries expect (e.g., "Order" for "order")
        sql_table_name = _to_sql_table_name(key)
        
        # Create table with the SQL table name (SQLite is case-insensitive, so this works for both)
        # This ensures queries using "Order" will work even if data key is "order"
        create_and_insert(conn, sql_table_name, row_list)
        
        # Also create with original key name if different (for tools that might use it)
        table = str(key)
        if sql_table_name.lower() != table.lower():
            create_and_insert(conn, table, row_list)

        if add_lowercase_alias:
            lower = table.lower()
            if lower != table:
                create_and_insert(conn, lower, row_list)

    conn.commit()
