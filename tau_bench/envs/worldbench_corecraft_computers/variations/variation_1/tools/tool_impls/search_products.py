import json
from typing import Annotated, List, Optional, Union

from models import Product
from pydantic import Field
from utils import get_db_conn


def searchProducts(
    category: Annotated[
        Optional[str],
        Field(
            description="Product category (cpu, motherboard, gpu, memory, storage, psu, case, cooling, prebuilt, workstation, monitor, keyboard, mouse, headset, networking, cable, accessory, bundle)"
        ),
    ] = None,
    brand: Annotated[Optional[str], Field(description="Product brand name")] = None,
    min_price: Annotated[
        Optional[float], Field(description="Minimum price filter")
    ] = None,
    max_price: Annotated[
        Optional[float], Field(description="Maximum price filter")
    ] = None,
    price: Annotated[
        Optional[float], Field(description="Eact price filter")
    ] = None,
    inStockOnly: Annotated[
        Optional[str], Field(description="Only return products with inventory > 0")
    ] = None,
    minStock: Annotated[
        Optional[float], Field(description="Minimum stock level filter")
    ] = None,
    maxStock: Annotated[
        Optional[float], Field(description="Maximum stock level filter")
    ] = None,
    text: Annotated[
        Optional[str], Field(description="Text search across name, brand, and SKU")
    ] = None,
    limit: Annotated[
        Optional[float],
        Field(description="Maximum number of results (default 50, max 200)"),
    ] = None,
    product_id: Annotated[
        Optional[str], Field(description="Exact product ID filter")
    ] = None,
) -> List[Product]:
    """Search for products with various filters
Returns an array of product records matching the criteria"""
    limit = int(limit) if limit else 50
    limit = min(limit, 200)

    conditions = []
    params = []

    if category:
        conditions.append("category = ?")
        params.append(category)

    if brand:
        conditions.append("brand = ?")
        params.append(brand)

    if min_price is not None:
        conditions.append("price >= ?")
        params.append(min_price)

    if max_price is not None:
        conditions.append("price <= ?")
        params.append(max_price)

    if price is not None:
        conditions.append("price = ?")
        params.append(price)

    if inStockOnly:
        conditions.append("json_extract(inventory, '$.inStock') > 0")

    if minStock is not None:
        conditions.append("json_extract(inventory, '$.inStock') >= ?")
        params.append(minStock)

    if maxStock is not None:
        conditions.append("json_extract(inventory, '$.inStock') <= ?")
        params.append(maxStock)

    if product_id:
        conditions.append("id = ?")
        params.append(product_id)

    if text:
        conditions.append("(name LIKE ? OR brand LIKE ? OR sku LIKE ?)")
        params.extend([f"%{text}%", f"%{text}%", f"%{text}%"])

    params.append(limit)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM Product {where_clause} ORDER BY name ASC, id ASC LIMIT ?"

    conn = get_db_conn()
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()

        # Convert rows to Product instances
        results = []
        for row in rows:
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
            
            results.append(Product(**row_dict))
        
        return results
    finally:
        conn.close()

