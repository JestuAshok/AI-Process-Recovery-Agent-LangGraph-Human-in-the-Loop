from typing import TypedDict, List, Dict, Any, Optional


class RecoveryState(TypedDict):
    """
    LangGraph state schema for autonomous business workflow recovery.
    Maintains complete context across failure detection, root cause analysis,
    recovery planning, human approvals, controlled tool execution, and verification.
    """
    workflow_id: str
    customer_id: str
    current_step: str
    workflow_status: str  # PENDING, RUNNING, FAILED, RECOVERING, WAITING_FOR_APPROVAL, COMPLETED, CANCELLED
    
    # Failure Details
    failure_type: Optional[str]
    error_code: Optional[str]
    error_message: Optional[str]
    step_id: Optional[int]
    
    # Root Cause & AI Analysis
    root_cause: Optional[str]
    severity: Optional[str]  # LOW, MEDIUM, HIGH, CRITICAL
    recovery_options: List[str]
    recommended_action: Optional[str]
    recommended_tool: Optional[str]
    tool_parameters: Dict[str, Any]
    ai_reasoning: Optional[str]
    impact_summary: Optional[str]
    
    # Recovery Plan
    recovery_plan: List[Dict[str, Any]]
    selected_recovery: Optional[str]
    
    # Approval Flow
    approval_required: bool
    approval_status: Optional[str]  # PENDING, APPROVED, REJECTED, NOT_REQUIRED
    approval_id: Optional[int]
    approved_by: Optional[str]
    approval_comments: Optional[str]
    
    # Execution & Verification
    execution_result: Dict[str, Any]
    verification_result: Dict[str, Any]
    is_verified: bool
    retry_count: int
    max_retries: int
    
    # Audit trail accumulator for the execution cycle
    audit_events: List[Dict[str, Any]]
    
    # Metadata context
    metadata: Dict[str, Any]
