from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.db import get_db
from backend.database.models import Failure, RecoveryAction
from backend.schemas.schemas import FailureOut, RecoveryActionOut

router = APIRouter(prefix="/api", tags=["Failures & Recovery Actions"])


@router.get("/failures", response_model=List[FailureOut])
def list_failures(
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, RECOVERED, UNRESOLVED"),
    severity: Optional[str] = Query(None, description="Filter by severity: LOW, MEDIUM, HIGH, CRITICAL"),
    db: Session = Depends(get_db)
):
    """Lists detected failures and their root causes."""
    query = db.query(Failure)
    if status:
        query = query.filter(Failure.status == status.upper())
    if severity:
        query = query.filter(Failure.severity == severity.upper())
    return query.order_by(desc(Failure.detected_at)).all()


@router.get("/recovery-actions", response_model=List[RecoveryActionOut])
def list_recovery_actions(
    status: Optional[str] = Query(None, description="Filter by status: PROPOSED, APPROVED, EXECUTED, VERIFIED, REJECTED"),
    db: Session = Depends(get_db)
):
    """Lists recovery actions proposed and executed by the AI Agent."""
    query = db.query(RecoveryAction)
    if status:
        query = query.filter(RecoveryAction.status == status.upper())
    return query.order_by(desc(RecoveryAction.id)).all()
