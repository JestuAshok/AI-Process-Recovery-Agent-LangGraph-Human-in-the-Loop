import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models import Base, Workflow, WorkflowStep
from backend.workflow_engine.engine import workflow_engine

# Use in-memory SQLite for testing
test_engine = create_engine("sqlite:///:memory:", echo=False)
TestingSessionLocal = sessionmaker(bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def test_workflow_initialization():
    db = TestingSessionLocal()
    try:
        wf = workflow_engine.create_workflow(
            db=db,
            customer_id="CUST-TEST-01",
            product_id="PROD-MONITOR-4K",
            quantity=1,
            unit_price=499.50
        )
        assert wf.workflow_id.startswith("ORD-") or wf.workflow_id.startswith("WF-")
        assert wf.status == "PENDING"
        assert len(wf.steps) == 5
    finally:
        db.close()


def test_workflow_healthy_execution_to_completion():
    db = TestingSessionLocal()
    try:
        # Use available product PROD-MONITOR-4K
        wf = workflow_engine.create_workflow(
            db=db,
            customer_id="CUST-HEALTHY",
            product_id="PROD-MONITOR-4K",
            quantity=1,
            unit_price=499.50
        )
        completed_wf = workflow_engine.run_workflow(db, wf.workflow_id)
        assert completed_wf.status == "COMPLETED"
        assert completed_wf.current_step == "COMPLETED"
    finally:
        db.close()


def test_workflow_out_of_stock_failure_and_approval_gate():
    db = TestingSessionLocal()
    try:
        # PROD-LAPTOP-X1 is out of stock -> triggers failure & approval gate
        wf = workflow_engine.create_workflow(
            db=db,
            customer_id="CUST-STOCK-TEST",
            product_id="PROD-LAPTOP-X1",
            quantity=1,
            unit_price=1299.99,
            force_failure_scenario="OUT_OF_STOCK"
        )
        stopped_wf = workflow_engine.run_workflow(db, wf.workflow_id)
        assert stopped_wf.status == "WAITING_FOR_APPROVAL"
        assert len(stopped_wf.approvals) == 1
        assert stopped_wf.approvals[0].approval_status == "PENDING"

        # Now test human approval resolution
        appr_id = stopped_wf.approvals[0].id
        approved_wf = workflow_engine.approve_recovery(
            db=db,
            approval_id=appr_id,
            approved_by="Test Operator",
            comments="Approved substitution for testing."
        )
        assert approved_wf.status == "COMPLETED"
    finally:
        db.close()
