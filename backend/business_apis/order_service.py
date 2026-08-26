import uuid
import datetime
from fastapi import APIRouter, HTTPException
from backend.schemas.schemas import OrderCreateRequest, OrderUpdateRequest
from backend.business_apis.state import business_state

router = APIRouter(prefix="/api/business/orders", tags=["Business - Order API"])


@router.post("")
def create_order(req: OrderCreateRequest):
    """Creates a new simulated customer order."""
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    order_data = {
        "order_id": order_id,
        "workflow_id": req.workflow_id,
        "customer_id": req.customer_id,
        "items": req.items,
        "total_amount": req.total_amount,
        "shipping_address": req.shipping_address,
        "status": "CREATED",
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    business_state.orders[order_id] = order_data
    business_state.record_metric("order", success=True, latency=25)
    return order_data


@router.get("/{order_id}")
def get_order(order_id: str):
    """Retrieves order details by order_id or workflow_id."""
    if order_id in business_state.orders:
        return business_state.orders[order_id]

    for oid, data in business_state.orders.items():
        if data.get("workflow_id") == order_id:
            return data

    business_state.record_metric("order", success=False, latency=15)
    raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")


@router.put("/{order_id}")
def update_order(order_id: str, req: OrderUpdateRequest):
    """
    Updates order payload - used during recovery to replace out-of-stock items,
    update quantities, or adjust pricing.
    """
    target = None
    target_id = order_id
    if order_id in business_state.orders:
        target = business_state.orders[order_id]
    else:
        for oid, data in business_state.orders.items():
            if data.get("workflow_id") == order_id:
                target = data
                target_id = oid
                break

    if not target:
        raise HTTPException(status_code=404, detail=f"Order '{order_id}' not found.")

    if req.replacement_product_id:
        # Swap product in items list
        alt_prod = business_state.products.get(req.replacement_product_id)
        prod_name = alt_prod["name"] if alt_prod else "Replacement Product"
        target["items"] = [{
            "product_id": req.replacement_product_id,
            "name": prod_name,
            "quantity": req.new_quantity or 1,
            "unit_price": alt_prod["unit_price"] if alt_prod else target["total_amount"]
        }]
        target["replaced_from_previous"] = True
        target["active_product_id"] = req.replacement_product_id

    if req.new_total_amount is not None:
        target["total_amount"] = req.new_total_amount
    if req.shipping_address:
        target["shipping_address"] = req.shipping_address
    if req.status:
        target["status"] = req.status

    target["updated_at"] = datetime.datetime.utcnow().isoformat()
    business_state.orders[target_id] = target
    business_state.record_metric("order", success=True, latency=30)
    return target


@router.post("/{order_id}/cancel")
def cancel_order(order_id: str, reason: str = "Unrecoverable workflow failure"):
    """Cancels the customer order."""
    target = None
    if order_id in business_state.orders:
        target = business_state.orders[order_id]
    else:
        for oid, data in business_state.orders.items():
            if data.get("workflow_id") == order_id:
                target = data
                break

    if target:
        target["status"] = "CANCELLED"
        target["cancellation_reason"] = reason
        return {"status": "CANCELLED", "order_id": target["order_id"], "reason": reason}

    return {"status": "CANCELLED", "order_id": order_id, "reason": reason}
