import uuid
import time
from fastapi import APIRouter, HTTPException
from backend.schemas.schemas import PaymentProcessRequest, PaymentProcessResponse
from backend.business_apis.state import business_state

router = APIRouter(prefix="/api/business/payment", tags=["Business - Payment API"])


@router.post("/process", response_model=PaymentProcessResponse)
def process_payment(req: PaymentProcessRequest):
    """
    Simulates payment processing.
    Handles success, timeout, card declined, and 503 service unavailable scenarios.
    """
    active_fault = business_state.is_fault_active("payment")
    fault = req.force_failure or active_fault

    payment_id = f"PAY-{uuid.uuid4().hex[:8].upper()}"

    if fault == "TIMEOUT":
        business_state.record_metric("payment", success=False, latency=4500)
        # Record payment record as timeout
        business_state.payments[payment_id] = {
            "payment_id": payment_id,
            "workflow_id": req.workflow_id,
            "status": "TIMEOUT",
            "amount": req.amount,
            "error_code": "PAYMENT_GATEWAY_TIMEOUT",
            "message": "Payment gateway took > 4000ms to respond. Transaction in unknown state."
        }
        return PaymentProcessResponse(
            payment_id=payment_id,
            status="TIMEOUT",
            amount=req.amount,
            message="Payment gateway timed out. Please retry or verify status."
        )

    elif fault == "DECLINED":
        business_state.record_metric("payment", success=False, latency=120)
        business_state.payments[payment_id] = {
            "payment_id": payment_id,
            "workflow_id": req.workflow_id,
            "status": "DECLINED",
            "amount": req.amount,
            "error_code": "CARD_DECLINED_INSUFFICIENT_FUNDS",
            "message": "Card declined: Insufficient funds or fraud check triggered."
        }
        return PaymentProcessResponse(
            payment_id=payment_id,
            status="DECLINED",
            amount=req.amount,
            message="Card issuer declined transaction."
        )

    elif fault == "SERVICE_UNAVAILABLE" or fault == "service_down":
        business_state.record_metric("payment", success=False, latency=800)
        raise HTTPException(
            status_code=503,
            detail="Payment processor cluster is temporarily unavailable (503 Service Unavailable)."
        )

    # Success case
    business_state.record_metric("payment", success=True, latency=45)
    record = {
        "payment_id": payment_id,
        "workflow_id": req.workflow_id,
        "customer_id": req.customer_id,
        "status": "SUCCESS",
        "amount": req.amount,
        "currency": "USD",
        "payment_method": req.payment_method,
        "timestamp": time.time()
    }
    business_state.payments[payment_id] = record

    return PaymentProcessResponse(
        payment_id=payment_id,
        status="SUCCESS",
        amount=req.amount,
        currency="USD",
        message="Payment processed and captured successfully."
    )


@router.get("/status/{payment_id}")
def get_payment_status(payment_id: str):
    """Verifies payment transaction status."""
    if payment_id not in business_state.payments:
        # Search by workflow_id if needed
        for pid, data in business_state.payments.items():
            if data.get("workflow_id") == payment_id:
                return data
        return {"payment_id": payment_id, "status": "NOT_FOUND", "message": "Transaction record not found"}
    return business_state.payments[payment_id]


@router.post("/refund/{payment_id}")
def refund_payment(payment_id: str):
    """Processes refund for cancelled orders or price differences."""
    if payment_id in business_state.payments:
        business_state.payments[payment_id]["status"] = "REFUNDED"
        return {"payment_id": payment_id, "status": "REFUNDED", "message": "Payment refunded in full."}
    return {"payment_id": payment_id, "status": "REFUNDED", "message": "Simulated refund applied."}
