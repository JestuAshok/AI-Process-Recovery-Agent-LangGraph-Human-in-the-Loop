import datetime
from typing import List
from fastapi import APIRouter, HTTPException
from backend.schemas.schemas import ChaosInjectRequest, ServiceHealthResponse
from backend.business_apis.state import business_state

router = APIRouter(prefix="/api/services", tags=["Business Services & Chaos Simulator"])


@router.get("/health", response_model=List[ServiceHealthResponse])
def get_services_health():
    """Returns real-time health, latency, request volume, and active chaos flags for all simulated services."""
    res = []
    display_names = {
        "payment": "Payment Gateway API",
        "inventory": "Warehouse Inventory Service",
        "order": "Order Processing Hub",
        "delivery": "Carrier Logistics API",
        "notification": "Customer Notification Relay"
    }

    for s_key, stats in business_state.service_stats.items():
        active_fault = business_state.is_fault_active(s_key)
        status = "DEGRADED" if active_fault else stats.get("status", "HEALTHY")
        res.append(ServiceHealthResponse(
            service_name=display_names.get(s_key, s_key.capitalize()),
            status=status,
            response_time_ms=stats.get("latency_ms", 40),
            request_count=stats.get("requests", 0),
            failure_count=stats.get("failures", 0),
            active_chaos_fault=active_fault,
            last_checked=datetime.datetime.utcnow()
        ))
    return res


@router.post("/chaos/inject")
def inject_chaos_fault(req: ChaosInjectRequest):
    """
    Intentionally injects faults (timeout, out-of-stock, service 503, carrier down)
    to demonstrate live recovery capabilities.
    """
    valid_services = ["payment", "inventory", "order", "delivery", "notification"]
    svc = req.service_name.lower()
    if svc not in valid_services:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service name '{req.service_name}'. Valid options: {valid_services}"
        )

    business_state.inject_fault(svc, req.fault_type, req.duration_seconds)
    return {
        "status": "FAULT_INJECTED",
        "service": svc,
        "fault_type": req.fault_type,
        "duration_seconds": req.duration_seconds,
        "message": f"Chaos fault '{req.fault_type}' active on {svc} for {req.duration_seconds}s."
    }


@router.post("/chaos/reset")
def reset_all_chaos():
    """Clears all active chaos faults and restores services to healthy state."""
    business_state.clear_all_faults()
    return {"status": "RESET", "message": "All injected chaos faults cleared. Microservices restored to normal."}
