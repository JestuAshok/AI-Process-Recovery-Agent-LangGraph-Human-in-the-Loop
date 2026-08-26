import json
import datetime
from sqlalchemy.orm import Session
from backend.database.db import SessionLocal, init_db
from backend.database.models import (
    Workflow,
    WorkflowStep,
    Failure,
    RecoveryAction,
    Approval,
    AuditLog,
    ServiceMetric
)
from backend.business_apis.state import business_state

SEED_WORKFLOWS = [
    # 1. Fully Recovered Out-of-Stock Workflow (Historical completed recovery with manager approval)
    {
        "workflow_id": "ORD-IN-BLR-MACBOOK-101",
        "order_name": "Apple MacBook Air M3 (13.6\", 16GB RAM, 512GB Upgrade)",
        "customer_id": "CUST-IN-BLR-RAVI",
        "workflow_type": "ONLINE_ORDER",
        "status": "COMPLETED",
        "current_step": "COMPLETED",
        "total_amount": 99900.00,
        "product_id": "PROD-LAPTOP-X2",
        "delivery_address": "Flat 402, Green Glen Layout, Bellandur, Bengaluru, Karnataka - 560103",
        "delivery_carrier": "Blue Dart Express",
        "created_mins_ago": 120,
        "scenario": "OUT_OF_STOCK_RECOVERED"
    },
    # 2. Fully Recovered Payment Timeout Workflow (UPI / Razorpay auto-retry)
    {
        "workflow_id": "ORD-IN-HYD-SAMSUNG-102",
        "order_name": "Samsung 32-inch 4K UHD Smart Curved Monitor",
        "customer_id": "CUST-IN-HYD-ANANYA",
        "workflow_type": "ONLINE_ORDER",
        "status": "COMPLETED",
        "current_step": "COMPLETED",
        "total_amount": 44999.00,
        "product_id": "PROD-MONITOR-4K",
        "delivery_address": "Plot 18, Road 36, Jubilee Hills, Hyderabad, Telangana - 500033",
        "delivery_carrier": "Ekart Logistics (Flipkart)",
        "created_mins_ago": 95,
        "scenario": "PAYMENT_RETRY_RECOVERED"
    },
    # 3. Active Pending Approval Workflow (Waiting for Manager in Approval Gate!)
    {
        "workflow_id": "ORD-IN-MUM-MACBOOK-103",
        "order_name": "Apple MacBook Air M3 (13.6\", 8GB, 256GB SSD)",
        "customer_id": "CUST-IN-MUM-PRIYA",
        "workflow_type": "ONLINE_ORDER",
        "status": "WAITING_FOR_APPROVAL",
        "current_step": "INVENTORY_CHECK",
        "total_amount": 99900.00,
        "product_id": "PROD-LAPTOP-X1",
        "delivery_address": "B-204, Oberoi Springs, Andheri West, Mumbai, Maharashtra - 400053",
        "delivery_carrier": "Blue Dart Express",
        "created_mins_ago": 15,
        "scenario": "PENDING_APPROVAL_SUBSTITUTION"
    },
    # 4. Currently Recovering Carrier Reroute Workflow (Delhivery to Blue Dart switch)
    {
        "workflow_id": "ORD-IN-DEL-IPHONE-104",
        "order_name": "Apple iPhone 15 Pro Max (256 GB) - Natural Titanium",
        "customer_id": "CUST-IN-DEL-ROHIT",
        "workflow_type": "ONLINE_ORDER",
        "status": "RECOVERING",
        "current_step": "DELIVERY_SCHEDULING",
        "total_amount": 144900.00,
        "product_id": "PROD-PHONE-MAX",
        "delivery_address": "14 Barakhamba Road, Connaught Place, New Delhi - 110001",
        "delivery_carrier": "Blue Dart Express",
        "created_mins_ago": 8,
        "scenario": "CARRIER_SWITCH_ACTIVE"
    },
    # 5. Normal Healthy Completed Order 1
    {
        "workflow_id": "ORD-IN-PUN-IPHONE-105",
        "order_name": "Apple iPhone 15 Pro Max (256 GB) - Natural Titanium",
        "customer_id": "CUST-IN-PUN-KAVITA",
        "workflow_type": "ONLINE_ORDER",
        "status": "COMPLETED",
        "current_step": "COMPLETED",
        "total_amount": 144900.00,
        "product_id": "PROD-PHONE-MAX",
        "delivery_address": "Lane 7, Koregaon Park, Pune, Maharashtra - 411001",
        "delivery_carrier": "Amazon Shipping Priority",
        "created_mins_ago": 180,
        "scenario": "HEALTHY_COMPLETED"
    },
    # 6. Normal Healthy Completed Order 2
    {
        "workflow_id": "ORD-IN-CHE-SAMSUNG-106",
        "order_name": "Samsung 32-inch 4K UHD Smart Curved Monitor",
        "customer_id": "CUST-IN-CHE-KARTHIK",
        "workflow_type": "ONLINE_ORDER",
        "status": "COMPLETED",
        "current_step": "COMPLETED",
        "total_amount": 44999.00,
        "product_id": "PROD-MONITOR-4K",
        "delivery_address": "Tower 3, Tidel Park, OMR, Chennai, Tamil Nadu - 600113",
        "delivery_carrier": "Delhivery Express",
        "created_mins_ago": 150,
        "scenario": "HEALTHY_COMPLETED"
    },
    # 7. Unresolved / Failed Workflow (High-Risk Payment Alert)
    {
        "workflow_id": "ORD-IN-NOIDA-MACBOOK-107",
        "order_name": "Apple MacBook Pro 16-inch M3 Max (36GB, 1TB SSD)",
        "customer_id": "CUST-IN-NOIDA-UNKNOWN",
        "workflow_type": "ONLINE_ORDER",
        "status": "FAILED",
        "current_step": "PAYMENT_PROCESSING",
        "total_amount": 349900.00,
        "product_id": "PROD-LAPTOP-ULTRA",
        "delivery_address": "Sector 62, Noida, Uttar Pradesh - 201309",
        "delivery_carrier": "Delhivery Express",
        "created_mins_ago": 45,
        "scenario": "CARD_FRAUD_FAILED"
    },
    # 8. High Value Pending Approval (₹3,49,900 VIP dual-key sign-off needed)
    {
        "workflow_id": "ORD-IN-GGN-MACBOOK-108",
        "order_name": "Apple MacBook Pro 16-inch M3 Max VIP Corporate Fleet",
        "customer_id": "CUST-IN-GGN-VIKRAM",
        "workflow_type": "ONLINE_ORDER",
        "status": "WAITING_FOR_APPROVAL",
        "current_step": "INVENTORY_CHECK",
        "total_amount": 349900.00,
        "product_id": "PROD-LAPTOP-ULTRA",
        "delivery_address": "DLF Cyber City, Building 10, Gurugram, Haryana - 122002",
        "delivery_carrier": "Blue Dart Express",
        "created_mins_ago": 5,
        "scenario": "HIGH_VALUE_APPROVAL"
    },
    # 9. Normal Healthy In-Flight Order (Running)
    {
        "workflow_id": "ORD-IN-KOL-IPHONE-109",
        "order_name": "Apple iPhone 15 Pro Max (256 GB) - Natural Titanium",
        "customer_id": "CUST-IN-KOL-SOURAV",
        "workflow_type": "ONLINE_ORDER",
        "status": "RUNNING",
        "current_step": "ORDER_CONFIRMATION",
        "total_amount": 144900.00,
        "product_id": "PROD-PHONE-MAX",
        "delivery_address": "Block EP & GP, Sector V, Salt Lake, Kolkata, West Bengal - 700091",
        "delivery_carrier": "Ekart Logistics (Flipkart)",
        "created_mins_ago": 2,
        "scenario": "RUNNING_HEALTHY"
    },
    # 10. Pending Order in Queue
    {
        "workflow_id": "ORD-IN-BLR-SAMSUNG-110",
        "order_name": "Samsung 32-inch 4K UHD Smart Curved Monitor",
        "customer_id": "CUST-IN-BLR-DEEPAK",
        "workflow_type": "ONLINE_ORDER",
        "status": "PENDING",
        "current_step": "ORDER_CREATED",
        "total_amount": 44999.00,
        "product_id": "PROD-MONITOR-4K",
        "delivery_address": "100 Feet Road, Indiranagar, Bengaluru, Karnataka - 560038",
        "delivery_carrier": "Amazon Shipping Priority",
        "created_mins_ago": 1,
        "scenario": "PENDING_NEW"
    }
]

STEP_NAMES = ["ORDER_CREATED", "PAYMENT_PROCESSING", "INVENTORY_CHECK", "ORDER_CONFIRMATION", "DELIVERY_SCHEDULING"]


def seed_database(db: Session = None):
    """Populates database with initial rich test dataset."""
    own_session = False
    if db is None:
        init_db()
        db = SessionLocal()
        own_session = True

    try:
        # Check if already seeded
        if db.query(Workflow).count() > 0:
            print("Database already contains records. Skipping seed.")
            return

        print("Seeding initial Indian e-commerce workflows and service metrics...")

        # 1. Seed Service Metrics (Indian Gateways & Couriers)
        services_init = [
            ("UPI / Razorpay Payment Gateway", "HEALTHY", 38, 2840, 12),
            ("Warehouse Hub Inventory API (Bengaluru)", "HEALTHY", 29, 3950, 18),
            ("Order Management Hub", "HEALTHY", 24, 4650, 4),
            ("Blue Dart & Delhivery Logistics Dispatch", "HEALTHY", 45, 2390, 14),
            ("SMS & WhatsApp Notification Relay", "HEALTHY", 18, 5220, 1)
        ]
        for name, st, lat, reqs, fails in services_init:
            sm = ServiceMetric(
                service_name=name,
                status=st,
                response_time_ms=lat,
                request_count=reqs,
                failure_count=fails,
                last_checked=datetime.datetime.utcnow()
            )
            db.add(sm)

        # 2. Seed Workflows
        now = datetime.datetime.utcnow()

        for item in SEED_WORKFLOWS:
            created_at = now - datetime.timedelta(minutes=item["created_mins_ago"])
            metadata = {
                "order_name": item.get("order_name", f"Order {item['workflow_id']}"),
                "customer_id": item["customer_id"],
                "product_id": item["product_id"],
                "quantity": 1,
                "unit_price": item["total_amount"],
                "total_amount": item["total_amount"],
                "delivery_address": item.get("delivery_address", "Bellandur, Bengaluru, Karnataka - 560103"),
                "delivery_carrier": item.get("delivery_carrier", "Blue Dart Express")
            }

            wf = Workflow(
                workflow_id=item["workflow_id"],
                customer_id=item["customer_id"],
                workflow_type=item["workflow_type"],
                status=item["status"],
                current_step=item["current_step"],
                total_amount=item["total_amount"],
                metadata_json=json.dumps(metadata),
                created_at=created_at,
                updated_at=created_at + datetime.timedelta(minutes=2)
            )
            db.add(wf)
            db.flush()

            # Seed Steps
            for idx, sname in enumerate(STEP_NAMES, 1):
                step_status = "SUCCESS" if item["status"] == "COMPLETED" else "PENDING"
                if item["status"] == "WAITING_FOR_APPROVAL" and sname == "INVENTORY_CHECK":
                    step_status = "FAILED"
                elif item["status"] == "RECOVERING" and sname == "DELIVERY_SCHEDULING":
                    step_status = "RECOVERING"
                elif item["status"] == "FAILED" and sname == "PAYMENT_PROCESSING":
                    step_status = "FAILED"

                wstep = WorkflowStep(
                    workflow_id=item["workflow_id"],
                    step_name=sname,
                    step_order=idx,
                    status=step_status,
                    started_at=created_at + datetime.timedelta(seconds=idx * 15),
                    completed_at=created_at + datetime.timedelta(seconds=idx * 30) if step_status == "SUCCESS" else None
                )
                db.add(wstep)
                db.flush()

            # Seed Failure, RecoveryAction, Approval, and Audit Logs based on Scenario
            if item["scenario"] == "PENDING_APPROVAL_SUBSTITUTION":
                fail = Failure(
                    workflow_id=item["workflow_id"],
                    step_name="INVENTORY_CHECK",
                    failure_type="OUT_OF_STOCK",
                    error_code="ERR_INVENTORY_DEPLETED",
                    root_cause="Bengaluru Hub warehouse stock for 256GB MacBook Air depleted. AI matched 512GB Upgrade edition (PROD-LAPTOP-X2) with 18 units in stock at ₹0 price difference.",
                    severity="HIGH",
                    retry_count=0,
                    detected_at=created_at + datetime.timedelta(seconds=45),
                    status="ACTIVE"
                )
                db.add(fail)
                db.flush()

                rec = RecoveryAction(
                    workflow_id=item["workflow_id"],
                    failure_id=fail.id,
                    proposed_action="Free Upgrade: Substitute with Apple MacBook Air M3 (16GB RAM, 512GB SSD) at ₹0 extra cost",
                    reasoning="Protects delivery SLA. Upgraded model has 2x RAM & 2x Storage with 18 units ready in Whitefield Fulfillment Hub.",
                    action_type="REPLACE_PRODUCT",
                    tool_name="find_alternative_product",
                    parameters_json=json.dumps({"product_id": "PROD-LAPTOP-X1"}),
                    status="PROPOSED",
                    executed_at=None
                )
                db.add(rec)
                db.flush()

                appr = Approval(
                    workflow_id=item["workflow_id"],
                    recovery_action_id=rec.id,
                    approval_status="PENDING",
                    risk_level="MEDIUM",
                    proposed_action="Replace out-of-stock 256GB MacBook with 512GB Upgrade Edition",
                    reasoning="Identical customer color preference (Space Grey), 16GB RAM + 512GB SSD upgrade, zero additional charge to buyer.",
                    impact_summary="₹0 customer charge delta, protects CSAT, 18 units available in hub.",
                    created_at=created_at + datetime.timedelta(seconds=50)
                )
                db.add(appr)

                audits = [
                    ("WORKFLOW_INITIALIZED", "SYSTEM", f"Order {item['workflow_id']} placed for ₹{item['total_amount']:,.2f}"),
                    ("PAYMENT_CAPTURED", "SYSTEM", "Payment ₹99,900.00 received via UPI (Google Pay / HDFC)."),
                    ("FAILURE_DETECTED", "AI_AGENT", "Autonomous Agent detected stock shortage at 'INVENTORY_CHECK': ERR_INVENTORY_DEPLETED"),
                    ("ROOT_CAUSE_IDENTIFIED", "AI_AGENT", "Root Cause: 256GB model stock=0 in Bengaluru hub."),
                    ("RECOVERY_PLAN_CREATED", "AI_AGENT", "Recovery Plan: Catalog scan -> 512GB Upgrade matched -> Human Approval Gate -> Order update"),
                    ("APPROVAL_REQUESTED", "AI_AGENT", "Free product upgrade sent to Approval Gate for Operations Manager sign-off.")
                ]
                for ev, actor, msg in audits:
                    db.add(AuditLog(
                        workflow_id=item["workflow_id"],
                        event_type=ev,
                        actor=actor,
                        message=msg,
                        timestamp=created_at + datetime.timedelta(seconds=10)
                    ))

            elif item["scenario"] == "OUT_OF_STOCK_RECOVERED":
                fail = Failure(
                    workflow_id=item["workflow_id"],
                    step_name="INVENTORY_CHECK",
                    failure_type="OUT_OF_STOCK",
                    error_code="ERR_INVENTORY_DEPLETED",
                    root_cause="Primary 256GB model out of stock. Autonomous catalog scan identified 512GB Upgrade model PROD-LAPTOP-X2.",
                    severity="MEDIUM",
                    status="RECOVERED"
                )
                db.add(fail)
                db.flush()

                rec = RecoveryAction(
                    workflow_id=item["workflow_id"],
                    failure_id=fail.id,
                    proposed_action="Free Upgrade: Substitute with MacBook Air M3 512GB Upgrade Edition",
                    reasoning="Approved by E-Commerce Operations Director.",
                    action_type="REPLACE_PRODUCT",
                    tool_name="find_alternative_product",
                    status="VERIFIED",
                    executed_at=created_at + datetime.timedelta(seconds=70),
                    result_json=json.dumps({"success": True, "active_product_id": "PROD-LAPTOP-X2"})
                )
                db.add(rec)
                db.flush()

                appr = Approval(
                    workflow_id=item["workflow_id"],
                    recovery_action_id=rec.id,
                    approval_status="APPROVED",
                    risk_level="MEDIUM",
                    approved_by="Rajesh Sharma (Operations Director)",
                    comments="Approved 512GB upgrade substitution to protect Amazon/Flipkart same-day SLA.",
                    created_at=created_at + datetime.timedelta(seconds=30),
                    resolved_at=created_at + datetime.timedelta(seconds=60)
                )
                db.add(appr)

                audits = [
                    ("WORKFLOW_INITIALIZED", "SYSTEM", f"Order {item['workflow_id']} placed for ₹{item['total_amount']:,.2f}"),
                    ("FAILURE_DETECTED", "AI_AGENT", "Stock depletion detected at INVENTORY_CHECK: ERR_INVENTORY_DEPLETED"),
                    ("ROOT_CAUSE_IDENTIFIED", "AI_AGENT", "Root Cause: SKU unavailable in local fulfillment hub."),
                    ("APPROVAL_GRANTED", "HUMAN_OPERATOR", "Operations Manager approved replacement product."),
                    ("RECOVERY_ACTION_EXECUTED", "AI_AGENT", "Allocated upgraded MacBook Air 512GB PROD-LAPTOP-X2."),
                    ("RECOVERY_VERIFIED", "AI_AGENT", "Bengaluru Hub reserved unit. Verification passed 100%."),
                    ("WORKFLOW_COMPLETED", "SYSTEM", "Order dispatched via Blue Dart Express (Tracking: BD-BLR-98421).")
                ]
                for ev, actor, msg in audits:
                    db.add(AuditLog(
                        workflow_id=item["workflow_id"],
                        event_type=ev,
                        actor=actor,
                        message=msg,
                        timestamp=created_at + datetime.timedelta(seconds=40)
                    ))

            elif item["scenario"] == "CARRIER_SWITCH_ACTIVE":
                fail = Failure(
                    workflow_id=item["workflow_id"],
                    step_name="DELIVERY_SCHEDULING",
                    failure_type="DELIVERY_FAILED",
                    error_code="ERR_LOGISTICS_CARRIER_OFFLINE",
                    root_cause="Delhivery API dispatch endpoint timed out. AI agent executed automatic failover to Blue Dart Express.",
                    severity="MEDIUM",
                    status="ACTIVE"
                )
                db.add(fail)
                db.flush()

                rec = RecoveryAction(
                    workflow_id=item["workflow_id"],
                    failure_id=fail.id,
                    proposed_action="Reroute parcel dispatch to Blue Dart Express Priority",
                    reasoning="Delhivery gateway unreachable; Blue Dart Express verified online with next-morning delivery guarantee.",
                    action_type="SWITCH_CARRIER",
                    tool_name="schedule_delivery",
                    parameters_json=json.dumps({"carrier": "Blue Dart Express"}),
                    status="EXECUTED",
                    executed_at=created_at + datetime.timedelta(seconds=30)
                )
                db.add(rec)

            elif item["scenario"] == "CARD_FRAUD_FAILED":
                fail = Failure(
                    workflow_id=item["workflow_id"],
                    step_name="PAYMENT_PROCESSING",
                    failure_type="CARD_FRAUD_FAILED",
                    error_code="ERR_PAYMENT_FRAUD_FLAG",
                    root_cause="Razorpay fraud engine flagged transaction: multiple rapid high-value card attempts from untrusted IP. Authorization declined.",
                    severity="CRITICAL",
                    status="UNRESOLVED"
                )
                db.add(fail)

            elif item["scenario"] == "PAYMENT_RETRY_RECOVERED":
                fail = Failure(
                    workflow_id=item["workflow_id"],
                    step_name="PAYMENT_PROCESSING",
                    failure_type="PAYMENT_TIMEOUT",
                    error_code="ERR_PAYMENT_GATEWAY_TIMEOUT",
                    root_cause="Primary UPI gateway response exceeded 4000ms SLA. AI switched to HDFC Bank backup route and confirmed payment.",
                    severity="MEDIUM",
                    status="RECOVERED"
                )
                db.add(fail)
                db.flush()

                rec = RecoveryAction(
                    workflow_id=item["workflow_id"],
                    failure_id=fail.id,
                    proposed_action="Retry payment via HDFC Bank Secondary Gateway Node",
                    reasoning="Primary UPI Route timed out; HDFC Direct Node verified online with 38ms latency.",
                    action_type="RETRY_PAYMENT",
                    tool_name="process_payment",
                    status="VERIFIED",
                    executed_at=created_at + datetime.timedelta(seconds=20)
                )
                db.add(rec)

            elif item["scenario"] == "HIGH_VALUE_APPROVAL":
                appr = Approval(
                    workflow_id=item["workflow_id"],
                    approval_status="PENDING",
                    risk_level="HIGH",
                    proposed_action="Authorize VIP ₹3,49,900 MacBook Pro M3 Max dispatch & dedicated secure transit",
                    reasoning="Orders above ₹2,50,000 require dual-key compliance sign-off per security policy.",
                    impact_summary="₹3,49,900 transaction value; high-security tamper-evident packaging required.",
                    created_at=created_at + datetime.timedelta(seconds=20)
                )
                db.add(appr)
                db.add(AuditLog(
                    workflow_id=item["workflow_id"],
                    event_type="APPROVAL_REQUESTED",
                    actor="AI_AGENT",
                    message="High-value compliance threshold (₹2,50,000) exceeded. Senior Director sign-off requested.",
                    timestamp=created_at
                ))

            else:
                db.add(AuditLog(
                    workflow_id=item["workflow_id"],
                    event_type="WORKFLOW_COMPLETED" if item["status"] == "COMPLETED" else "WORKFLOW_INITIALIZED",
                    actor="SYSTEM",
                    message=f"Order status: {item['status']} for ₹{item['total_amount']:,.2f}",
                    timestamp=created_at
                ))

        db.commit()
        print("Database seeding completed successfully with 10 Indian e-commerce workflows.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    seed_database()

