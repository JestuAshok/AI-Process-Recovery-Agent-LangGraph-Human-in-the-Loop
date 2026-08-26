from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from backend.schemas.schemas import InventoryItemResponse
from backend.business_apis.state import business_state

router = APIRouter(prefix="/api/business/inventory", tags=["Business - Inventory API"])


@router.get("/{product_id}", response_model=InventoryItemResponse)
def check_inventory(product_id: str, force_out_of_stock: Optional[bool] = False):
    """
    Checks real-time inventory level for a specified product.
    Returns availability, stock quantity, specifications, and alternative products.
    """
    fault = business_state.is_fault_active("inventory")
    if fault == "service_down" or fault == "INVENTORY_SERVICE_DOWN":
        business_state.record_metric("inventory", success=False, latency=1200)
        raise HTTPException(
            status_code=503,
            detail="Inventory Service cluster degraded (503 Service Unavailable). Warehouse database unresponsive."
        )

    if product_id not in business_state.products:
        business_state.record_metric("inventory", success=False, latency=30)
        raise HTTPException(status_code=404, detail=f"Product with ID '{product_id}' not found in catalog.")

    product = business_state.products[product_id]
    is_oos = force_out_of_stock or fault == "out_of_stock" or product["stock_quantity"] <= 0

    # Build alternatives list with live stock info
    alternatives_data: List[Dict[str, Any]] = []
    for alt_id in product.get("alternatives", []):
        if alt_id in business_state.products:
            alt = business_state.products[alt_id]
            alternatives_data.append({
                "product_id": alt["product_id"],
                "name": alt["name"],
                "unit_price": alt["unit_price"],
                "stock_quantity": alt["stock_quantity"],
                "available": alt["stock_quantity"] > 0,
                "specifications": alt.get("specifications", {})
            })

    business_state.record_metric("inventory", success=True, latency=35)

    return InventoryItemResponse(
        product_id=product["product_id"],
        name=product["name"],
        available=not is_oos,
        stock_quantity=0 if is_oos else product["stock_quantity"],
        unit_price=product["unit_price"],
        category=product["category"],
        specifications=product.get("specifications", {}),
        alternatives=alternatives_data
    )


@router.get("", response_model=List[InventoryItemResponse])
def list_all_products():
    """Lists all products in the catalog."""
    res = []
    for pid in business_state.products:
        res.append(check_inventory(pid))
    return res


@router.post("/reserve/{product_id}")
def reserve_inventory(product_id: str, quantity: int = 1):
    """Reserves inventory quantity for an order."""
    if product_id not in business_state.products:
        raise HTTPException(status_code=404, detail="Product not found")

    prod = business_state.products[product_id]
    if prod["stock_quantity"] < quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reserve {quantity} units. Only {prod['stock_quantity']} units available."
        )

    prod["stock_quantity"] -= quantity
    return {
        "status": "RESERVED",
        "product_id": product_id,
        "quantity_reserved": quantity,
        "remaining_stock": prod["stock_quantity"]
    }
