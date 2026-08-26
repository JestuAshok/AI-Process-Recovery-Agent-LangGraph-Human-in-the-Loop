import uuid
import datetime
from fastapi import APIRouter
from backend.schemas.schemas import NotificationSendRequest
from backend.business_apis.state import business_state

router = APIRouter(prefix="/api/business/notification", tags=["Business - Notification API"])


@router.post("/send")
def send_notification(req: NotificationSendRequest):
    """
    Sends customer notification via Email, SMS, or Push.
    Used by agent to inform customer regarding recovery decisions, approvals, or order updates.
    """
    notif_id = f"NOTIF-{uuid.uuid4().hex[:8].upper()}"
    record = {
        "notification_id": notif_id,
        "workflow_id": req.workflow_id,
        "recipient": req.recipient,
        "channel": req.channel,
        "subject": req.subject,
        "content": req.content,
        "status": "DELIVERED",
        "sent_at": datetime.datetime.utcnow().isoformat()
    }
    business_state.notifications.append(record)
    business_state.record_metric("notification", success=True, latency=20)
    return {
        "status": "SENT",
        "notification_id": notif_id,
        "channel": req.channel,
        "recipient": req.recipient,
        "message": "Notification dispatched to customer successfully."
    }


@router.get("/logs")
def get_notification_logs(workflow_id: str = None):
    """Lists dispatched customer notifications."""
    if workflow_id:
        return [n for n in business_state.notifications if n.get("workflow_id") == workflow_id]
    return business_state.notifications[-50:]
