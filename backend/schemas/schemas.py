import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# -------------------------------------------------------------
# Base & Common Schemas
# -------------------------------------------------------------
class WorkflowStepOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: str
    step_name: str
    step_order: int
    status: str
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    payload_json: Optional[str] = "{}"
    started_at: Optional[datetime.datetime] = None
    completed_at: Optional[datetime.datetime] = None


class FailureOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: str
    step_id: Optional[int] = None
    step_name: Optional[str] = None
    failure_type: str
    error_code: str
    root_cause: Optional[str] = None
    severity: str
    retry_count: int
    detected_at: datetime.datetime
    status: str


class RecoveryActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: str
    failure_id: Optional[int] = None
    proposed_action: str
    reasoning: str
    action_type: str
    tool_name: str
    parameters_json: Optional[str] = "{}"
    status: str
    executed_at: Optional[datetime.datetime] = None
    result_json: Optional[str] = "{}"


class ApprovalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: str
    recovery_action_id: Optional[int] = None
    approval_status: str
    risk_level: str
    proposed_action: Optional[str] = None
    reasoning: Optional[str] = None
    impact_summary: Optional[str] = None
    approved_by: Optional[str] = None
    comments: Optional[str] = None
    created_at: datetime.datetime
    resolved_at: Optional[datetime.datetime] = None


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: str
    event_type: str
    actor: str
    message: str
    details_json: Optional[str] = "{}"
    timestamp: datetime.datetime


class WorkflowOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: str
    customer_id: str
    workflow_type: str
    status: str
    current_step: str
    total_amount: float
    metadata_json: Optional[str] = "{}"
    created_at: datetime.datetime
    updated_at: datetime.datetime


class WorkflowDetailOut(WorkflowOut):
    steps: List[WorkflowStepOut] = []
    failures: List[FailureOut] = []
    recovery_actions: List[RecoveryActionOut] = []
    approvals: List[ApprovalOut] = []
    audit_logs: List[AuditLogOut] = []


class WorkflowCreateRequest(BaseModel):
    customer_id: str = "CUST-8801"
    product_id: str = "PROD-LAPTOP-X1"
    quantity: int = 1
    unit_price: float = 1299.99
    delivery_address: str = "742 Evergreen Terrace, Springfield, OR"
    delivery_carrier: str = "EXPRESS_AIR"
    force_failure_scenario: Optional[str] = None  # None, "PAYMENT_TIMEOUT", "OUT_OF_STOCK", "INVENTORY_SERVICE_DOWN", "DELIVERY_FAILED", "HIGH_VALUE_REFUND"


# -------------------------------------------------------------
# Structured AI Agent Schemas (Root-Cause & Recovery Plan)
# -------------------------------------------------------------
class RootCauseAnalysis(BaseModel):
    failure_type: str = Field(description="Classification of the failure, e.g., PAYMENT_FAILURE, INVENTORY_FAILURE, DELIVERY_FAILURE")
    root_cause: str = Field(description="Clear human-readable root cause explanation")
    severity: str = Field(description="LOW, MEDIUM, HIGH, or CRITICAL")
    recovery_options: List[str] = Field(description="List of viable recovery strategies")
    recommended_action: str = Field(description="The optimal recovery tool to invoke")
    recommended_tool: str = Field(description="Function tool name to execute, e.g. find_alternative_product, retry_payment")
    tool_parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters to pass to the tool")
    approval_required: bool = Field(description="True if action exceeds risk threshold or business policy")
    risk_assessment: str = Field(description="Explanation of why approval is or is not required")
    impact_summary: str = Field(description="Expected impact on customer, inventory, and cost")


class RecoveryPlanStep(BaseModel):
    step_number: int
    action_name: str
    description: str
    requires_approval: bool = False


class RecoveryPlan(BaseModel):
    workflow_id: str
    failure_summary: str
    root_cause: str
    steps: List[RecoveryPlanStep]
    selected_tool: str
    tool_parameters: Dict[str, Any] = Field(default_factory=dict)
    approval_required: bool
    ai_reasoning: str


# -------------------------------------------------------------
# Human Approval Decision Schema
# -------------------------------------------------------------
class ApprovalDecisionRequest(BaseModel):
    approved_by: str = "Senior Operations Manager"
    comments: Optional[str] = "Approved alternative product replacement to maintain customer SLA."


# -------------------------------------------------------------
# Simulated Business API Request & Response Schemas
# -------------------------------------------------------------
class PaymentProcessRequest(BaseModel):
    workflow_id: str
    customer_id: str
    amount: float
    payment_method: str = "CREDIT_CARD"
    card_token: str = "tok_visa_4242"
    force_failure: Optional[str] = None  # TIMEOUT, DECLINED, SERVICE_UNAVAILABLE


class PaymentProcessResponse(BaseModel):
    payment_id: str
    status: str  # SUCCESS, TIMEOUT, DECLINED, SERVICE_UNAVAILABLE
    amount: float
    currency: str = "USD"
    message: str
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)


class InventoryItemResponse(BaseModel):
    product_id: str
    name: str
    available: bool
    stock_quantity: int
    unit_price: float
    category: str
    specifications: Dict[str, Any] = {}
    alternatives: List[Dict[str, Any]] = []


class OrderCreateRequest(BaseModel):
    workflow_id: str
    customer_id: str
    items: List[Dict[str, Any]]
    total_amount: float
    shipping_address: str


class OrderUpdateRequest(BaseModel):
    order_id: str
    replacement_product_id: Optional[str] = None
    new_quantity: Optional[int] = None
    new_total_amount: Optional[float] = None
    shipping_address: Optional[str] = None
    status: Optional[str] = None


class DeliveryScheduleRequest(BaseModel):
    workflow_id: str
    order_id: str
    carrier: str = "FedEx Express"
    recipient_address: str
    package_weight_kg: float = 2.5
    force_failure: Optional[str] = None  # SERVICE_UNAVAILABLE, ROUTE_BLOCKED


class DeliveryScheduleResponse(BaseModel):
    tracking_number: str
    status: str  # SCHEDULED, SERVICE_UNAVAILABLE, FAILED
    carrier: str
    estimated_delivery: str
    message: str


class NotificationSendRequest(BaseModel):
    workflow_id: str
    recipient: str
    channel: str = "EMAIL"  # EMAIL, SMS, PUSH
    subject: str
    content: str


# -------------------------------------------------------------
# Chaos Fault Injection & Service Health Schemas
# -------------------------------------------------------------
class ChaosInjectRequest(BaseModel):
    service_name: str  # payment, inventory, delivery, order, notification
    fault_type: str  # timeout, out_of_stock, service_down, high_latency, carrier_down
    duration_seconds: int = 60


class ServiceHealthResponse(BaseModel):
    service_name: str
    status: str
    response_time_ms: int
    request_count: int
    failure_count: int
    active_chaos_fault: Optional[str] = None
    last_checked: datetime.datetime


# -------------------------------------------------------------
# Demo Run Schemas
# -------------------------------------------------------------
class DemoScenarioRequest(BaseModel):
    scenario_id: str  # payment_timeout, inventory_out_of_stock, inventory_service_down, delivery_failed, high_value_recovery
    auto_approve: bool = False
