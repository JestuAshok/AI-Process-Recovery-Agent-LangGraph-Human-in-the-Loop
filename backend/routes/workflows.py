import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.db import get_db
from backend.database.models import Workflow, WorkflowStep, Failure, RecoveryAction, Approval, AuditLog
from backend.schemas.schemas import (
    WorkflowOut,
    WorkflowDetailOut,
    WorkflowCreateRequest
)
from backend.workflow_engine.engine import workflow_engine

router = APIRouter(prefix="/api/workflows", tags=["Workflows"])


@router.get("", response_model=List[WorkflowOut])
def list_workflows(
    status: Optional[str] = Query(None, description="Filter by status, e.g., PENDING, RUNNING, FAILED, WAITING_FOR_APPROVAL, COMPLETED"),
    search: Optional[str] = Query(None, description="Search by workflow_id or customer_id"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Lists all workflows with optional status filtering and search."""
    query = db.query(Workflow)
    if status:
        query = query.filter(Workflow.status == status.upper())
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Workflow.workflow_id.ilike(search_pattern)) | (Workflow.customer_id.ilike(search_pattern))
        )
    return query.order_by(desc(Workflow.created_at)).limit(limit).all()


@router.get("/stats")
def get_workflow_stats(db: Session = Depends(get_db)):
    """Computes KPI metrics for dashboard."""
    total = db.query(Workflow).count()
    active = db.query(Workflow).filter(Workflow.status.in_(["RUNNING", "PENDING"])).count()
    failed = db.query(Workflow).filter(Workflow.status == "FAILED").count()
    recovering = db.query(Workflow).filter(Workflow.status == "RECOVERING").count()
    completed = db.query(Workflow).filter(Workflow.status == "COMPLETED").count()
    pending_approvals = db.query(Approval).filter(Approval.approval_status == "PENDING").count()

    # Recovery success rate
    total_failures = db.query(Failure).count()
    recovered_failures = db.query(Failure).filter(Failure.status == "RECOVERED").count()
    success_rate = round((recovered_failures / max(1, total_failures)) * 100, 1)

    return {
        "total_workflows": total,
        "active_workflows": active,
        "failed_workflows": failed,
        "recovering_workflows": recovering,
        "completed_workflows": completed,
        "pending_approvals": pending_approvals,
        "recovered_failures": recovered_failures,
        "recovery_success_rate": success_rate
    }


@router.get("/{workflow_id}", response_model=WorkflowDetailOut)
def get_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Retrieves full workflow details with steps, failures, recovery actions, approvals, and audit logs."""
    wf = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")
    return wf


@router.post("", response_model=WorkflowDetailOut)
def create_workflow(req: WorkflowCreateRequest, db: Session = Depends(get_db)):
    """Creates and initializes a new business workflow."""
    wf = workflow_engine.create_workflow(
        db=db,
        customer_id=req.customer_id,
        product_id=req.product_id,
        quantity=req.quantity,
        unit_price=req.unit_price,
        delivery_address=req.delivery_address,
        delivery_carrier=req.delivery_carrier,
        force_failure_scenario=req.force_failure_scenario
    )
    return wf


@router.post("/{workflow_id}/start", response_model=WorkflowDetailOut)
def start_workflow(workflow_id: str, db: Session = Depends(get_db)):
    """Executes the workflow step by step, auto-invoking recovery on failure."""
    try:
        wf = workflow_engine.run_workflow(db, workflow_id)
        return wf
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution error: {str(e)}")


@router.post("/{workflow_id}/recover", response_model=WorkflowDetailOut)
def trigger_workflow_recovery(workflow_id: str, db: Session = Depends(get_db)):
    """Manually re-triggers AI Recovery Agent on a failed workflow."""
    wf = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")

    metadata = json.loads(wf.metadata_json or "{}")
    step = db.query(WorkflowStep).filter(
        WorkflowStep.workflow_id == workflow_id,
        WorkflowStep.status == "FAILED"
    ).first()

    if not step:
        # Run workflow from beginning
        return workflow_engine.run_workflow(db, workflow_id)

    return workflow_engine._handle_step_failure(
        db, wf, step, step.error_code or "MANUAL_RECOVERY_TRIGGER", step.error_message or "Manual recovery requested", metadata
    )


@router.get("/{workflow_id}/timeline")
def get_workflow_timeline(workflow_id: str, db: Session = Depends(get_db)):
    """Provides a chronological timeline representation of the workflow lifecycle."""
    wf = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found.")

    steps = db.query(WorkflowStep).filter(WorkflowStep.workflow_id == workflow_id).order_by(WorkflowStep.step_order).all()
    failures = db.query(Failure).filter(Failure.workflow_id == workflow_id).all()
    recovery_actions = db.query(RecoveryAction).filter(RecoveryAction.workflow_id == workflow_id).all()
    approvals = db.query(Approval).filter(Approval.workflow_id == workflow_id).all()
    logs = db.query(AuditLog).filter(AuditLog.workflow_id == workflow_id).order_by(AuditLog.timestamp.asc()).all()

    return {
        "workflow_id": workflow_id,
        "status": wf.status,
        "current_step": wf.current_step,
        "steps": steps,
        "failures": failures,
        "recovery_actions": recovery_actions,
        "approvals": approvals,
        "audit_logs": logs
    }
