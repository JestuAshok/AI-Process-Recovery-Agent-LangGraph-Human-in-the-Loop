import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database.db import get_db
from backend.schemas.schemas import DemoScenarioRequest, WorkflowDetailOut
from backend.workflow_engine.engine import workflow_engine
from backend.database.models import Workflow

router = APIRouter(prefix="/api/demo", tags=["Demo Scenarios Orchestrator"])

DEMO_SCENARIO_CONFIGS = {
    "inventory_out_of_stock": {
        "title": "Demo 1: Bangalore Hub Stock Depletion (Auto 512GB Upgrade)",
        "description": "Customer ordered 256GB MacBook Air M3, but regional hub ran out of stock. AI scans catalog, finds 512GB Upgrade model at ₹0 extra cost, routes to Approval Gate, and completes order.",
        "product_id": "PROD-LAPTOP-X1",
        "quantity": 1,
        "unit_price": 99900.00,
        "customer_id": "CUST-IN-BLR",
        "force_failure": "OUT_OF_STOCK",
        "requires_human_approval": True
    },
    "payment_timeout": {
        "title": "Demo 2: UPI / Razorpay Payment Timeout (Auto-Retry via HDFC Backup)",
        "description": "UPI / Netbanking payment gateway response exceeds 4000ms SLA. AI intercepts failure, switches to HDFC Bank backup route, confirms payment, and dispatches invoice.",
        "product_id": "PROD-MONITOR-4K",
        "quantity": 1,
        "unit_price": 44999.00,
        "customer_id": "CUST-IN-HYD",
        "force_failure": "PAYMENT_TIMEOUT",
        "requires_human_approval": False
    },
    "inventory_service_down": {
        "title": "Demo 3: Mumbai Hub Warehouse Microservice Outage (503 Auto-Reconnect)",
        "description": "Warehouse stock allocation microservice throws HTTP 503 error. AI detects infrastructure degradation, applies exponential backoff, reconnects to Mumbai hub, and resumes fulfillment.",
        "product_id": "PROD-PHONE-MAX",
        "quantity": 1,
        "unit_price": 144900.00,
        "customer_id": "CUST-IN-MUM",
        "force_failure": "INVENTORY_SERVICE_DOWN",
        "requires_human_approval": False
    },
    "delivery_failed": {
        "title": "Demo 4: Delhivery Courier Hub Disconnect (Auto-Switch to Blue Dart)",
        "description": "Delhivery dispatch API stalls. AI agent detects delivery stall, reroutes order parcel to Blue Dart Express with same-day tracking manifest, and completes shipment.",
        "product_id": "PROD-PHONE-MAX",
        "quantity": 1,
        "unit_price": 144900.00,
        "customer_id": "CUST-IN-DEL",
        "force_failure": "DELIVERY_FAILED",
        "requires_human_approval": False
    },
    "high_value_recovery": {
        "title": "Demo 5: High-Value Order Governance (₹3,49,900 Dual-Approval Gate)",
        "description": "High-value ₹3,49,900 MacBook Pro M3 Max order triggers Amazon/Flipkart high-value security policy requiring dual-key senior operations director approval.",
        "product_id": "PROD-LAPTOP-ULTRA",
        "quantity": 1,
        "unit_price": 349900.00,
        "customer_id": "CUST-IN-VIP",
        "force_failure": "HIGH_VALUE_REFUND",
        "requires_human_approval": True
    }
}


@router.get("/scenarios")
def list_demo_scenarios():
    """Lists all available interactive demo scenarios."""
    return [
        {"id": k, **v} for k, v in DEMO_SCENARIO_CONFIGS.items()
    ]


@router.post("/run-scenario", response_model=WorkflowDetailOut)
def run_demo_scenario(req: DemoScenarioRequest, db: Session = Depends(get_db)):
    """
    Launches an end-to-end interactive demo workflow scenario.
    """
    scen_id = req.scenario_id.lower()
    if scen_id not in DEMO_SCENARIO_CONFIGS:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown scenario '{req.scenario_id}'. Available: {list(DEMO_SCENARIO_CONFIGS.keys())}"
        )

    cfg = DEMO_SCENARIO_CONFIGS[scen_id]

    # Create workflow
    wf = workflow_engine.create_workflow(
        db=db,
        customer_id=f"{cfg['customer_id']}-{uuid.uuid4().hex[:4].upper()}",
        product_id=cfg["product_id"],
        quantity=cfg["quantity"],
        unit_price=cfg["unit_price"],
        delivery_address="777 Innovation Drive, Silicon Valley, CA",
        delivery_carrier="FedEx Express",
        force_failure_scenario=cfg["force_failure"]
    )

    # Execute workflow (will hit the simulated fault and trigger LangGraph AI Recovery)
    wf = workflow_engine.run_workflow(db, wf.workflow_id)

    # If auto_approve requested on scenarios requiring approval
    if req.auto_approve and wf.status == "WAITING_FOR_APPROVAL" and wf.approvals:
        appr = wf.approvals[0]
        wf = workflow_engine.approve_recovery(
            db=db,
            approval_id=appr.id,
            approved_by="Demo Auto-Approver",
            comments="Auto-approved for demonstration replay."
        )

    return wf
