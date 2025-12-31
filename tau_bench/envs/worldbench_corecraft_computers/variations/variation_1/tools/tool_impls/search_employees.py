import json
from typing import Annotated, List, Optional

from models import Employee
from pydantic import Field
from utils import get_db_conn


def searchEmployees(
    employee_id: Annotated[
        Optional[str],
        Field(description="Exact employee ID match")
    ] = None,
    name: Annotated[
        Optional[str],
        Field(description="Partial name search (case insensitive)")
    ] = None,
    department: Annotated[
        Optional[str],
        Field(description="Department to filter by. Valid values are \"operations\", \"order_processing\", \"engineering\", \"help_desk\", \"it_systems\", \"product_management\", \"finance\", and \"hr\".")
    ] = None,
    role: Annotated[Optional[str], Field(description="Role/title to search for")] = None,
    has_permission: Annotated[
        Optional[str],
        Field(description="Permission to filter by. Valid values are \"issue_refund\", \"edit_order\", \"cancel_order\", \"escalate\", \"kb_edit\", and \"policy_override\".")
    ] = None,
    limit: Annotated[
        Optional[float],
        Field(description="Maximum number of results (default 50, max 200)"),
    ] = None,
) -> List[Employee]:
    """Search for employees"""
    limit = int(limit) if limit else 50
    limit = min(limit, 200)

    conditions = []
    params = []

    if employee_id:
        conditions.append("id = ?")
        params.append(employee_id)

    if name:
        conditions.append("name LIKE ?")
        params.append(f"%{name}%")

    if department:
        conditions.append("department = ?")
        params.append(department)

    if role:
        conditions.append("title LIKE ?")
        params.append(f"%{role}%")

    if has_permission:
        # permissions is a JSON field, we need to search within it
        conditions.append("json_extract(permissions, '$') LIKE ?")
        params.append(f"%{has_permission}%")

    params.append(limit)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM Employee {where_clause} ORDER BY name ASC, id ASC LIMIT ?"

    conn = get_db_conn()

    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            row_dict = dict(row)

            # Parse JSON fields
            if "permissions" in row_dict and isinstance(row_dict["permissions"], str):
                try:
                    row_dict["permissions"] = json.loads(row_dict["permissions"])
                except (json.JSONDecodeError, TypeError):
                    pass

            results.append(Employee(**row_dict))

        return results
    finally:
        conn.close()
