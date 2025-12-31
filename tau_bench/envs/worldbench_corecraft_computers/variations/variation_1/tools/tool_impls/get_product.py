import json
from typing import Annotated, Any, Dict, Optional, Union

from pydantic import Field
from .utils import get_db_conn


def getProduct(
    product_id: Annotated[str, Field(description="The product_id parameter")],
) -> Optional[Dict[str, Any]]:
    """Get product by ID"""
    if not product_id:
        raise ValueError("product_id is required")

    conn = get_db_conn()

    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Product WHERE id = ?", [product_id])
        row = cursor.fetchone()

        if not row:
            return None

        row_dict = dict(row)

        # Parse JSON fields
        if "inventory" in row_dict and isinstance(row_dict["inventory"], str):
            try:
                row_dict["inventory"] = json.loads(row_dict["inventory"])
            except (json.JSONDecodeError, TypeError):
                pass

        if "specs" in row_dict and isinstance(row_dict["specs"], str):
            try:
                row_dict["specs"] = json.loads(row_dict["specs"])
            except (json.JSONDecodeError, TypeError):
                pass

        # Return as dict instead of Pydantic model to ensure None serializes correctly
        return row_dict
    finally:
        conn.close()
