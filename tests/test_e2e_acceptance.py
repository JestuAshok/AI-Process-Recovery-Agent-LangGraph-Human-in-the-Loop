import os
import sys
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from backend.database.db import init_db, SessionLocal
from backend.database.seed import seed_database
from backend.workflow_engine.engine import workflow_engine
from backend.database.models import Workflow, Failure, RecoveryAction, Approval, AuditLog


def run_full_acceptance_test():
    print("=" * 70)
    print("EXECUTING FORMAL END-TO-END ACCEPTANCE TEST (Prompt Section 42)")
    print("=" * 70)

    init_db()
    db = SessionLocal()

    try:
        # Clean up any previous test run record
        old = db.query(Workflow).filter(Workflow.workflow_id == "WF-DEMO-001").first()
        if old:
            db.delete(old)
            db.commit()

        # Step 1: Create Workflow WF-DEMO-001 with Out-of-Stock scenario
        print("\n[Step 1 & 2] Initializing workflow 'WF-DEMO-001' with forced OUT_OF_STOCK...")
        wf = workflow_engine.create_workflow(
            db=db,
            customer_id="CUST-ACME-ENTERPRISE",
            product_id="PROD-LAPTOP-X1",  # 0 stock
            quantity=1,
            unit_price=1299.99,
            force_failure_scenario="OUT_OF_STOCK",
            workflow_id="WF-DEMO-001"
        )
        print(f"-> Created Workflow: {wf.workflow_id} (Status: {wf.status})")

        # Step 2: Run Workflow -> Payment succeeds -> Inventory fails -> Agent analyzes -> Approval created
        print("\n[Step 3 to 10] Executing workflow lifecycle...")
        wf = workflow_engine.run_workflow(db, "WF-DEMO-001")
        print(f"-> Current Workflow Status: {wf.status}")
        print(f"-> Current Step: {wf.current_step}")

        assert wf.status == "WAITING_FOR_APPROVAL", f"Expected WAITING_FOR_APPROVAL, got {wf.status}"
        assert len(wf.approvals) >= 1, "Expected pending approval record"

        appr = wf.approvals[0]
        print(f"-> Approval Created ID: {appr.id}")
        print(f"   Proposed Action: {appr.proposed_action}")
        print(f"   Reasoning: {appr.reasoning}")
        print(f"   Risk Level: {appr.risk_level}")

        # Step 3: Human Operator Approves in Approval Center
        print("\n[Step 11 to 15] Operator clicks APPROVE RECOVERY in Approval Center...")
        wf = workflow_engine.approve_recovery(
            db=db,
            approval_id=appr.id,
            approved_by="Elena Vance (Chief Operations Officer)",
            comments="Approved automated laptop substitution to maintain 24h SLA."
        )

        print(f"-> Post-Approval Workflow Status: {wf.status}")
        print(f"-> Final Step: {wf.current_step}")

        assert wf.status == "COMPLETED", f"Expected COMPLETED, got {wf.status}"
        assert wf.current_step == "COMPLETED", f"Expected step COMPLETED, got {wf.current_step}"

        # Verify Audit Trail
        print("\n[Step 16 to 18] Inspecting Complete Audit Trail...")
        logs = db.query(AuditLog).filter(AuditLog.workflow_id == "WF-DEMO-001").order_by(AuditLog.timestamp.asc()).all()
        for idx, l in enumerate(logs, 1):
            print(f"  {idx:02d}. [{l.timestamp.strftime('%H:%M:%S')}] ({l.actor}) {l.event_type} -> {l.message}")

        event_types = [l.event_type for l in logs]
        required_events = [
            "WORKFLOW_INITIALIZED",
            "ORDER_CREATED",
            "PAYMENT_CAPTURED",
            "FAILURE_DETECTED",
            "ROOT_CAUSE_IDENTIFIED",
            "RECOVERY_PLAN_CREATED",
            "APPROVAL_REQUESTED",
            "APPROVAL_GRANTED",
            "RECOVERY_ACTION_EXECUTED",
            "RECOVERY_VERIFIED",
            "ORDER_CONFIRMED",
            "DELIVERY_SCHEDULED",
            "WORKFLOW_COMPLETED"
        ]

        for req in required_events:
            assert req in event_types, f"Missing required audit event: {req}"

        print("\n" + "=" * 70)
        print("ALL 18 ACCEPTANCE CRITERIA VERIFIED AND PASSED 100%!")
        print("=" * 70)

    finally:
        db.close()


if __name__ == "__main__":
    run_full_acceptance_test()
