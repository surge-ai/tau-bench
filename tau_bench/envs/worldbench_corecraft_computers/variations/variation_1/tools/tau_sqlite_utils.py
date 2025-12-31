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
    """Normalize supported row container shapes into a list of dict rows."""
    if rows is None:
        return []
    if isinstance(rows, list):
        return [r for r in rows if isinstance(r, dict)]
    if isinstance(rows, dict):
        return [r for r in rows.values() if isinstance(r, dict)]
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


def build_sqlite_from_data(conn: sqlite3.Connection, data: Dict[str, Any], *, add_lowercase_alias: bool = True) -> None:
    """Create one SQLite table per top-level key in `data` and insert its rows.

    If add_lowercase_alias=True, also creates a lowercase alias table if the key differs,
    to support tools that hardcode lowercase table names (e.g. `products`).
    """
    conn.row_factory = sqlite3.Row

    for key, rows in data.items():
        row_list = iter_rows(rows)
        if not row_list:
            continue

        table = str(key)
        create_and_insert(conn, table, row_list)

        if add_lowercase_alias:
            lower = table.lower()
            if lower != table:
                create_and_insert(conn, lower, row_list)

    conn.commit()
