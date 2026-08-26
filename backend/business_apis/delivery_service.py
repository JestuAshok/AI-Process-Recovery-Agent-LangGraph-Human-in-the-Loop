import uuid
import datetime
from fastapi import APIRouter, HTTPException
from backend.schemas.schemas import DeliveryScheduleRequest, DeliveryScheduleResponse
from backend.business_apis.state import business_state

router = APIRouter(prefix="/api/business/delivery", tags=["Business - Delivery API"])


@router.post("/schedule", response_model=DeliveryScheduleResponse)
def schedule_delivery(req: DeliveryScheduleRequest):
    """
    Schedules package delivery with logistics carriers.
    Supports primary carrier failure and seamless switchover to alternative carriers.
    """
    fault = business_state.is_fault_active("delivery")
    is_fault = req.force_failure or fault

    # If FedEx Express is failing in chaos mode
    if (is_fault == "SERVICE_UNAVAILABLE" or is_fault == "carrier_down") and req.carrier == "FedEx Express":
        business_state.record_metric("delivery", success=False, latency=1500)
        raise HTTPException(
            status_code=503,
            detail="Primary carrier (FedEx Express) dispatch gateway offline. Dispatch queue full."
        )

    # Alternate carrier or normal path succeeds
    tracking_num = f"TRK-{uuid.uuid4().hex[:10].upper()}"
    est_date = (datetime.datetime.utcnow() + datetime.timedelta(days=2)).strftime("%Y-%m-%d")

    delivery_record = {
        "tracking_number": tracking_num,
        "workflow_id": req.workflow_id,
        "order_id": req.order_id,
        "carrier": req.carrier,
        "status": "SCHEDULED",
        "recipient_address": req.recipient_address,
        "package_weight_kg": req.package_weight_kg,
        "estimated_delivery": est_date,
        "scheduled_at": datetime.datetime.utcnow().isoformat()
    }
    business_state.deliveries[tracking_num] = delivery_record
    business_state.record_metric("delivery", success=True, latency=65)

    return DeliveryScheduleResponse(
        tracking_number=tracking_num,
        status="SCHEDULED",
        carrier=req.carrier,
        estimated_delivery=est_date,
        message=f"Shipment successfully booked with {req.carrier}."
    )


@router.get("/carriers")
def list_available_carriers():
    """Lists available shipping carriers with real-time operational status."""
    carriers_list = []
    fault = business_state.is_fault_active("delivery")
    for name, data in business_state.carriers.items():
        status = "DEGRADED" if (fault and name == "FedEx Express") else data["status"]
        carriers_list.append({
            "name": name,
            "status": status,
            "avg_transit_days": data["avg_transit_days"],
            "cost": data["cost"],
            "recommended_alternative": (name == "UPS Next Day")
        })
    return carriers_list


@router.get("/tracking/{tracking_number}")
def get_delivery_status(tracking_number: str):
    """Checks delivery status."""
    if tracking_number in business_state.deliveries:
        return business_state.deliveries[tracking_number]
    for trk, data in business_state.deliveries.items():
        if data.get("workflow_id") == tracking_number or data.get("order_id") == tracking_number:
            return data
    raise HTTPException(status_code=404, detail="Tracking number not found")
