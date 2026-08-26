from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.db import get_db
from backend.database.models import Approval, Workflow
from backend.schemas.schemas import ApprovalOut, ApprovalDecisionRequest, WorkflowDetailOut
from backend.workflow_engine.engine import workflow_engine

router = APIRouter(prefix="/api/approvals", tags=["Human-in-the-Loop Approvals"])


@router.get("", response_model=List[ApprovalOut])
def list_approvals(
    status: Optional[str] = Query(None, description="Filter by status: PENDING, APPROVED, REJECTED"),
    db: Session = Depends(get_db)
):
    """Lists human approval requests."""
    query = db.query(Approval)
    if status:
        query = query.filter(Approval.approval_status == status.upper())
    return query.order_by(desc(Approval.created_at)).all()


@router.get("/{approval_id}", response_model=ApprovalOut)
def get_approval(approval_id: int, db: Session = Depends(get_db)):
    """Retrieves a single approval by ID."""
    appr = db.query(Approval).filter(Approval.id == approval_id).first()
    if not appr:
        raise HTTPException(status_code=404, detail=f"Approval with ID {approval_id} not found.")
    return appr


@router.post("/{approval_id}/approve", response_model=WorkflowDetailOut)
def approve_recovery_action(
    approval_id: int,
    req: ApprovalDecisionRequest = ApprovalDecisionRequest(),
    db: Session = Depends(get_db)
):
    """
    Human Approves the proposed AI recovery action.
    Resumes LangGraph execution, applies changes, verifies state, and completes the workflow.
    """
    try:
        wf = workflow_engine.approve_recovery(
            db=db,
            approval_id=approval_id,
            approved_by=req.approved_by,
            comments=req.comments or "Approved by operator."
        )
        return wf
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Approval execution error: {str(e)}")


@router.post("/{approval_id}/reject", response_model=WorkflowDetailOut)
def reject_recovery_action(
    approval_id: int,
    req: ApprovalDecisionRequest = ApprovalDecisionRequest(),
    db: Session = Depends(get_db)
):
    """
    Human Rejects the proposed AI recovery action.
    Terminates / cancels the workflow and records complete audit trail.
    """
    try:
        wf = workflow_engine.reject_recovery(
            db=db,
            approval_id=approval_id,
            rejected_by=req.approved_by,
            comments=req.comments or "Rejected by operator."
        )
        return wf
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rejection processing error: {str(e)}")
