from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.database.db import get_db
from backend.database.models import AuditLog
from backend.schemas.schemas import AuditLogOut

router = APIRouter(prefix="/api/audit-logs", tags=["Audit Logs"])


@router.get("", response_model=List[AuditLogOut])
def list_audit_logs(
    workflow_id: Optional[str] = Query(None, description="Filter logs for specific workflow"),
    actor: Optional[str] = Query(None, description="Filter by actor: AI_AGENT, HUMAN_OPERATOR, SYSTEM"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """Retrieves full chronological audit log records."""
    query = db.query(AuditLog)
    if workflow_id:
        query = query.filter(AuditLog.workflow_id == workflow_id)
    if actor:
        query = query.filter(AuditLog.actor == actor.upper())
    return query.order_by(desc(AuditLog.timestamp)).limit(limit).all()
