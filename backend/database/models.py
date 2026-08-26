import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from backend.database.db import Base


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(64), unique=True, index=True, nullable=False)
    customer_id = Column(String(64), nullable=False)
    workflow_type = Column(String(64), default="ONLINE_ORDER")
    status = Column(String(32), default="PENDING", index=True)  # PENDING, RUNNING, SUCCESS, FAILED, RECOVERING, WAITING_FOR_APPROVAL, CANCELLED, COMPLETED
    current_step = Column(String(64), default="ORDER_CREATED")
    total_amount = Column(Float, default=0.0)
    metadata_json = Column(Text, default="{}")  # stores items, customer info, delivery info, etc.
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStep.step_order")
    failures = relationship("Failure", back_populates="workflow", cascade="all, delete-orphan")
    recovery_actions = relationship("RecoveryAction", back_populates="workflow", cascade="all, delete-orphan")
    approvals = relationship("Approval", back_populates="workflow", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="workflow", cascade="all, delete-orphan", order_by="AuditLog.timestamp.desc()")


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(64), ForeignKey("workflows.workflow_id", ondelete="CASCADE"), nullable=False, index=True)
    step_name = Column(String(64), nullable=False)  # ORDER_CREATED, PAYMENT_PROCESSING, INVENTORY_CHECK, ORDER_CONFIRMATION, DELIVERY_SCHEDULING
    step_order = Column(Integer, default=1)
    status = Column(String(32), default="PENDING")  # PENDING, RUNNING, SUCCESS, FAILED, RECOVERING, WAITING_FOR_APPROVAL, COMPLETED
    error_code = Column(String(64), nullable=True)
    error_message = Column(Text, nullable=True)
    payload_json = Column(Text, default="{}")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    workflow = relationship("Workflow", back_populates="steps")


class Failure(Base):
    __tablename__ = "failures"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(64), ForeignKey("workflows.workflow_id", ondelete="CASCADE"), nullable=False, index=True)
    step_id = Column(Integer, ForeignKey("workflow_steps.id", ondelete="SET NULL"), nullable=True)
    step_name = Column(String(64), nullable=True)
    failure_type = Column(String(64), nullable=False)  # PAYMENT_TIMEOUT, OUT_OF_STOCK, INVENTORY_SERVICE_DOWN, DELIVERY_FAILED, etc.
    error_code = Column(String(64), nullable=False)
    root_cause = Column(Text, nullable=True)
    severity = Column(String(32), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    retry_count = Column(Integer, default=0)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    status = Column(String(32), default="ACTIVE")  # ACTIVE, RECOVERED, UNRESOLVED, ESCALATED

    workflow = relationship("Workflow", back_populates="failures")
    recovery_actions = relationship("RecoveryAction", back_populates="failure", cascade="all, delete-orphan")


class RecoveryAction(Base):
    __tablename__ = "recovery_actions"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(64), ForeignKey("workflows.workflow_id", ondelete="CASCADE"), nullable=False, index=True)
    failure_id = Column(Integer, ForeignKey("failures.id", ondelete="SET NULL"), nullable=True)
    proposed_action = Column(String(128), nullable=False)
    reasoning = Column(Text, nullable=False)
    action_type = Column(String(64), nullable=False)  # RETRY_PAYMENT, REPLACE_PRODUCT, SWITCH_CARRIER, BACKOFF_RETRY, CANCEL_ORDER
    tool_name = Column(String(64), nullable=False)
    parameters_json = Column(Text, default="{}")
    status = Column(String(32), default="PROPOSED")  # PROPOSED, APPROVED, EXECUTED, VERIFIED, FAILED, REJECTED
    executed_at = Column(DateTime, nullable=True)
    result_json = Column(Text, default="{}")

    workflow = relationship("Workflow", back_populates="recovery_actions")
    failure = relationship("Failure", back_populates="recovery_actions")
    approvals = relationship("Approval", back_populates="recovery_action", cascade="all, delete-orphan")


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(64), ForeignKey("workflows.workflow_id", ondelete="CASCADE"), nullable=False, index=True)
    recovery_action_id = Column(Integer, ForeignKey("recovery_actions.id", ondelete="SET NULL"), nullable=True)
    approval_status = Column(String(32), default="PENDING")  # PENDING, APPROVED, REJECTED, AUTO_APPROVED
    risk_level = Column(String(32), default="MEDIUM")  # LOW, MEDIUM, HIGH
    proposed_action = Column(String(128), nullable=True)
    reasoning = Column(Text, nullable=True)
    impact_summary = Column(Text, nullable=True)
    approved_by = Column(String(64), nullable=True)
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    workflow = relationship("Workflow", back_populates="approvals")
    recovery_action = relationship("RecoveryAction", back_populates="approvals")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(String(64), ForeignKey("workflows.workflow_id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)  # WORKFLOW_STARTED, FAILURE_DETECTED, ROOT_CAUSE_IDENTIFIED, PLAN_CREATED, APPROVAL_REQUESTED, APPROVAL_GRANTED, RECOVERY_EXECUTED, VERIFIED, COMPLETED
    actor = Column(String(64), default="AI_AGENT")  # AI_AGENT, SYSTEM, HUMAN_OPERATOR, CUSTOMER
    message = Column(Text, nullable=False)
    details_json = Column(Text, default="{}")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

    workflow = relationship("Workflow", back_populates="audit_logs")


class ServiceMetric(Base):
    __tablename__ = "service_metrics"

    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(64), unique=True, index=True, nullable=False)
    status = Column(String(32), default="HEALTHY")  # HEALTHY, DEGRADED, FAILING, RECOVERING
    response_time_ms = Column(Integer, default=45)
    request_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    last_checked = Column(DateTime, default=datetime.datetime.utcnow)
