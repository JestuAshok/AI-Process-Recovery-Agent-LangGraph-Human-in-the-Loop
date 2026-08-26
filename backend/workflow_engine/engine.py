import json
import uuid
import datetime
import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.database.models import Workflow, WorkflowStep, Failure, RecoveryAction, Approval, AuditLog
from backend.business_apis.state import business_state
from backend.business_apis.payment_service import process_payment
from backend.business_apis.inventory_service import check_inventory, reserve_inventory
from backend.business_apis.order_service import create_order, update_order
from backend.business_apis.delivery_service import schedule_delivery
from backend.business_apis.notification_service import send_notification
from backend.schemas.schemas import (
    PaymentProcessRequest,
    OrderCreateRequest,
    OrderUpdateRequest,
    DeliveryScheduleRequest,
    NotificationSendRequest
)
from backend.agent.graph import recovery_graph
from backend.agent.nodes import execute_action_node, verify_recovery_node

logger = logging.getLogger("workflow_engine")

WORKFLOW_STEPS_DEF = [
    (1, "ORDER_CREATED"),
    (2, "PAYMENT_PROCESSING"),
    (3, "INVENTORY_CHECK"),
    (4, "ORDER_CONFIRMATION"),
    (5, "DELIVERY_SCHEDULING")
]


class WorkflowEngine:
    """
    Core state machine orchestrating end-to-end business workflows,
    failure interception, and autonomous LangGraph agent recovery coordination.
    """

    def create_workflow(
        self,
        db: Session,
        customer_id: str = "CUST-8801",
        product_id: str = "PROD-LAPTOP-X1",
        quantity: int = 1,
        unit_price: float = 1299.99,
        delivery_address: str = "Flat 402, Green Glen Layout, Bellandur, Bengaluru, Karnataka - 560103",
        delivery_carrier: str = "Blue Dart Express",
        force_failure_scenario: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> Workflow:
        """Initializes a new workflow record with steps and audit log."""
        if not workflow_id:
            prefix_map = {
                "PROD-LAPTOP-X1": "ORD-IN-MACBOOK",
                "PROD-LAPTOP-X2": "ORD-IN-MACBOOK-PLUS",
                "PROD-LAPTOP-ULTRA": "ORD-IN-MACBOOK-ULTRA",
                "PROD-PHONE-MAX": "ORD-IN-IPHONE",
                "PROD-MONITOR-4K": "ORD-IN-SAMSUNG4K"
            }
            prefix = prefix_map.get(product_id, "ORD-IN-ORDER")
            workflow_id = f"{prefix}-{uuid.uuid4().hex[:4].upper()}"
        total_amount = round(quantity * unit_price, 2)

        product_names = {
            "PROD-LAPTOP-X1": "Apple MacBook Air M3 (13.6\", 8GB, 256GB SSD)",
            "PROD-LAPTOP-X2": "Apple MacBook Air M3 (13.6\", 16GB, 512GB Upgrade)",
            "PROD-LAPTOP-ULTRA": "Apple MacBook Pro 16-inch M3 Max (36GB, 1TB SSD)",
            "PROD-PHONE-MAX": "Apple iPhone 15 Pro Max (256 GB)",
            "PROD-MONITOR-4K": "Samsung 32-inch 4K UHD Smart Curved Monitor"
        }
        order_name = f"{product_names.get(product_id, 'Consumer Order')} - {customer_id}"

        metadata = {
            "order_name": order_name,
            "customer_id": customer_id,
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_amount": total_amount,
            "delivery_address": delivery_address,
            "delivery_carrier": delivery_carrier,
            "force_failure_scenario": force_failure_scenario
        }

        wf = Workflow(
            workflow_id=workflow_id,
            customer_id=customer_id,
            workflow_type="ONLINE_ORDER",
            status="PENDING",
            current_step="ORDER_CREATED",
            total_amount=total_amount,
            metadata_json=json.dumps(metadata),
            created_at=datetime.datetime.utcnow(),
            updated_at=datetime.datetime.utcnow()
        )
        db.add(wf)

        # Create step records
        for order, name in WORKFLOW_STEPS_DEF:
            step = WorkflowStep(
                workflow_id=workflow_id,
                step_name=name,
                step_order=order,
                status="PENDING" if order > 1 else "PENDING",
                payload_json=json.dumps(metadata)
            )
            db.add(step)

        # Initial Audit Log
        audit = AuditLog(
            workflow_id=workflow_id,
            event_type="WORKFLOW_INITIALIZED",
            actor="SYSTEM",
            message=f"Order workflow {workflow_id} created for customer {customer_id} (${total_amount:.2f})",
            details_json=json.dumps(metadata),
            timestamp=datetime.datetime.utcnow()
        )
        db.add(audit)
        db.commit()
        db.refresh(wf)
        return wf

    def run_workflow(self, db: Session, workflow_id: str) -> Workflow:
        """
        Executes the business workflow step-by-step.
        On step failure, automatically invokes the LangGraph AI Recovery Agent.
        """
        wf = db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
        if not wf:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        metadata = json.loads(wf.metadata_json or "{}")
        forced_fault = metadata.get("force_failure_scenario")

        wf.status = "RUNNING"
        db.commit()

        # Step 1: ORDER_CREATED
        s1 = self._get_step(db, workflow_id, "ORDER_CREATED")
        s1.status = "RUNNING"
        s1.started_at = datetime.datetime.utcnow()
        db.commit()

        try:
            # Call Order Service API
            prod_id = metadata.get("product_id", "PROD-LAPTOP-X1")
            ord_res = create_order(OrderCreateRequest(
                workflow_id=workflow_id,
                customer_id=wf.customer_id,
                items=[{"product_id": prod_id, "quantity": metadata.get("quantity", 1), "unit_price": metadata.get("unit_price", 1299.99)}],
                total_amount=wf.total_amount,
                shipping_address=metadata.get("delivery_address", "Springfield, OR")
            ))
            s1.status = "SUCCESS"
            s1.completed_at = datetime.datetime.utcnow()
            self._add_audit(db, workflow_id, "ORDER_CREATED", "SYSTEM", f"Order {ord_res.get('order_id')} successfully created in order management system.")
            db.commit()
        except Exception as e:
            return self._handle_step_failure(db, wf, s1, "ORDER_CREATION_FAILED", str(e), metadata)

        # Step 2: PAYMENT_PROCESSING
        s2 = self._get_step(db, workflow_id, "PAYMENT_PROCESSING")
        wf.current_step = "PAYMENT_PROCESSING"
        s2.status = "RUNNING"
        s2.started_at = datetime.datetime.utcnow()
        db.commit()

        # Check for simulated payment fault
        payment_force = "TIMEOUT" if forced_fault == "PAYMENT_TIMEOUT" else None
        try:
            pay_res = process_payment(PaymentProcessRequest(
                workflow_id=workflow_id,
                customer_id=wf.customer_id,
                amount=wf.total_amount,
                force_failure=payment_force
            ))

            if pay_res.status == "TIMEOUT":
                return self._handle_step_failure(db, wf, s2, "PAYMENT_GATEWAY_TIMEOUT", "Payment gateway timed out after 4000ms SLA limit.", metadata)
            elif pay_res.status == "DECLINED":
                return self._handle_step_failure(db, wf, s2, "PAYMENT_DECLINED", "Card declined by card network.", metadata)

            s2.status = "SUCCESS"
            s2.completed_at = datetime.datetime.utcnow()
            self._add_audit(db, workflow_id, "PAYMENT_CAPTURED", "SYSTEM", f"Payment {pay_res.payment_id} authorized and captured ($ {wf.total_amount:.2f}).")
            db.commit()
        except Exception as e:
            return self._handle_step_failure(db, wf, s2, "PAYMENT_SERVICE_UNAVAILABLE", str(e), metadata)

        # Step 3: INVENTORY_CHECK
        s3 = self._get_step(db, workflow_id, "INVENTORY_CHECK")
        wf.current_step = "INVENTORY_CHECK"
        s3.status = "RUNNING"
        s3.started_at = datetime.datetime.utcnow()
        db.commit()

        try:
            prod_id = metadata.get("product_id", "PROD-LAPTOP-X1")
            force_oos = (forced_fault == "OUT_OF_STOCK" or forced_fault == "HIGH_VALUE_REFUND")
            if forced_fault == "INVENTORY_SERVICE_DOWN":
                business_state.inject_fault("inventory", "service_down", 30)

            inv_res = check_inventory(prod_id, force_out_of_stock=force_oos)

            if not inv_res.available or inv_res.stock_quantity <= 0:
                return self._handle_step_failure(db, wf, s3, "OUT_OF_STOCK", f"Requested product '{prod_id}' ({inv_res.name}) has 0 units available in warehouse.", metadata)

            # Reserve stock
            reserve_inventory(prod_id, quantity=metadata.get("quantity", 1))
            s3.status = "SUCCESS"
            s3.completed_at = datetime.datetime.utcnow()
            self._add_audit(db, workflow_id, "INVENTORY_RESERVED", "SYSTEM", f"Inventory confirmed & reserved for '{inv_res.name}'.")
            db.commit()
        except Exception as e:
            return self._handle_step_failure(db, wf, s3, "INVENTORY_SERVICE_DOWN", str(e), metadata)

        # Step 4: ORDER_CONFIRMATION
        return self._complete_confirmation_and_delivery(db, wf, metadata, forced_fault)

    def _complete_confirmation_and_delivery(self, db: Session, wf: Workflow, metadata: Dict[str, Any], forced_fault: Optional[str]) -> Workflow:
        """Executes Order Confirmation and Delivery Scheduling steps."""
        workflow_id = wf.workflow_id

        # Step 4: ORDER_CONFIRMATION
        s4 = self._get_step(db, workflow_id, "ORDER_CONFIRMATION")
        wf.current_step = "ORDER_CONFIRMATION"
        s4.status = "RUNNING"
        s4.started_at = datetime.datetime.utcnow()
        db.commit()

        # Send confirmation email
        send_notification(NotificationSendRequest(
            workflow_id=workflow_id,
            recipient=f"{wf.customer_id.lower()}@example.com",
            channel="EMAIL",
            subject="Order Confirmed",
            content=f"Your order {workflow_id} has been confirmed."
        ))
        s4.status = "SUCCESS"
        s4.completed_at = datetime.datetime.utcnow()
        self._add_audit(db, workflow_id, "ORDER_CONFIRMED", "SYSTEM", f"Order confirmed and notification sent to {wf.customer_id}.")
        db.commit()

        # Step 5: DELIVERY_SCHEDULING
        s5 = self._get_step(db, workflow_id, "DELIVERY_SCHEDULING")
        wf.current_step = "DELIVERY_SCHEDULING"
        s5.status = "RUNNING"
        s5.started_at = datetime.datetime.utcnow()
        db.commit()

        carrier = metadata.get("delivery_carrier", "FedEx Express")
        force_delivery_fault = "SERVICE_UNAVAILABLE" if forced_fault == "DELIVERY_FAILED" else None

        try:
            deliv_res = schedule_delivery(DeliveryScheduleRequest(
                workflow_id=workflow_id,
                order_id=f"ORD-{workflow_id[-6:]}",
                carrier=carrier,
                recipient_address=metadata.get("delivery_address", "Springfield, OR"),
                force_failure=force_delivery_fault
            ))

            s5.status = "SUCCESS"
            s5.completed_at = datetime.datetime.utcnow()
            wf.status = "COMPLETED"
            wf.current_step = "COMPLETED"
            self._add_audit(db, workflow_id, "DELIVERY_SCHEDULED", "SYSTEM", f"Delivery booked with {deliv_res.carrier} (Tracking: {deliv_res.tracking_number}).")
            self._add_audit(db, workflow_id, "WORKFLOW_COMPLETED", "SYSTEM", f"Workflow {workflow_id} reached 100% completion successfully.")
            db.commit()
            return wf
        except Exception as e:
            return self._handle_step_failure(db, wf, s5, "DELIVERY_SERVICE_UNAVAILABLE", str(e), metadata)

    def _handle_step_failure(
        self,
        db: Session,
        wf: Workflow,
        step: WorkflowStep,
        error_code: str,
        error_message: str,
        metadata: Dict[str, Any]
    ) -> Workflow:
        """
        Intercepts step failure, registers Failure entity, and passes control to LangGraph Agent.
        """
        workflow_id = wf.workflow_id
        step.status = "FAILED"
        step.error_code = error_code
        step.error_message = error_message
        step.completed_at = datetime.datetime.utcnow()

        wf.status = "FAILED"
        wf.current_step = step.step_name
        db.commit()

        # 1. Create Failure Record in DB
        fail_rec = Failure(
            workflow_id=workflow_id,
            step_id=step.id,
            step_name=step.step_name,
            failure_type=error_code,
            error_code=error_code,
            root_cause=None,
            severity="MEDIUM",
            retry_count=0,
            detected_at=datetime.datetime.utcnow(),
            status="ACTIVE"
        )
        db.add(fail_rec)
        db.commit()
        db.refresh(fail_rec)

        # 2. Invoke LangGraph Recovery Agent
        initial_state = {
            "workflow_id": workflow_id,
            "customer_id": wf.customer_id,
            "current_step": step.step_name,
            "workflow_status": "FAILED",
            "failure_type": error_code,
            "error_code": error_code,
            "error_message": error_message,
            "step_id": step.id,
            "root_cause": None,
            "severity": "MEDIUM",
            "recovery_options": [],
            "recommended_action": None,
            "recommended_tool": None,
            "tool_parameters": {},
            "ai_reasoning": None,
            "impact_summary": None,
            "recovery_plan": [],
            "selected_recovery": None,
            "approval_required": False,
            "approval_status": "NOT_REQUIRED",
            "approval_id": None,
            "approved_by": None,
            "approval_comments": None,
            "execution_result": {},
            "verification_result": {},
            "is_verified": False,
            "retry_count": 0,
            "max_retries": 3,
            "audit_events": [],
            "metadata": metadata
        }

        logger.info(f"Invoking LangGraph Recovery Agent for workflow {workflow_id}...")
        final_state = recovery_graph.invoke(initial_state)

        # 3. Synchronize Agent State back into Database
        fail_rec.root_cause = final_state.get("root_cause")
        fail_rec.severity = final_state.get("severity", "MEDIUM")
        db.commit()

        # Sync Audit Events
        for ev in final_state.get("audit_events", []):
            audit = AuditLog(
                workflow_id=workflow_id,
                event_type=ev.get("event_type", "AGENT_ACTION"),
                actor=ev.get("actor", "AI_AGENT"),
                message=ev.get("message", ""),
                details_json=ev.get("details", "{}"),
                timestamp=datetime.datetime.utcnow()
            )
            db.add(audit)

        # Check if Recovery Action was planned
        if final_state.get("recommended_action"):
            rec_act = RecoveryAction(
                workflow_id=workflow_id,
                failure_id=fail_rec.id,
                proposed_action=final_state.get("recommended_action"),
                reasoning=final_state.get("ai_reasoning", "AI Selected Strategy"),
                action_type=final_state.get("recommended_tool", "TOOL"),
                tool_name=final_state.get("recommended_tool", "TOOL"),
                parameters_json=json.dumps(final_state.get("tool_parameters", {})),
                status="PROPOSED" if final_state.get("approval_required") and final_state.get("approval_status") == "PENDING" else "EXECUTED",
                executed_at=datetime.datetime.utcnow() if final_state.get("is_verified") else None,
                result_json=json.dumps(final_state.get("execution_result", {}))
            )
            db.add(rec_act)
            db.commit()
            db.refresh(rec_act)

            # Check if Approval Required
            if final_state.get("approval_required") and final_state.get("approval_status") == "PENDING":
                wf.status = "WAITING_FOR_APPROVAL"
                appr = Approval(
                    workflow_id=workflow_id,
                    recovery_action_id=rec_act.id,
                    approval_status="PENDING",
                    risk_level=final_state.get("severity", "MEDIUM"),
                    proposed_action=final_state.get("recommended_action"),
                    reasoning=final_state.get("ai_reasoning"),
                    impact_summary=final_state.get("impact_summary"),
                    created_at=datetime.datetime.utcnow()
                )
                db.add(appr)
                db.commit()
                return wf

        # If recovery was auto-executed and verified
        if final_state.get("is_verified"):
            fail_rec.status = "RECOVERED"
            step.status = "SUCCESS"
            db.commit()

            # Resume remaining workflow steps if we fixed an intermediate failure
            if step.step_name == "PAYMENT_PROCESSING":
                # Clear forced fault for subsequent steps and continue to inventory
                metadata["force_failure_scenario"] = None
                # Run remaining
                return self._continue_after_payment(db, wf, metadata)
            elif step.step_name == "INVENTORY_CHECK":
                metadata["force_failure_scenario"] = None
                return self._complete_confirmation_and_delivery(db, wf, metadata, None)
            elif step.step_name == "DELIVERY_SCHEDULING":
                wf.status = "COMPLETED"
                wf.current_step = "COMPLETED"
                db.commit()
                return wf

        db.commit()
        return wf

    def _continue_after_payment(self, db: Session, wf: Workflow, metadata: Dict[str, Any]) -> Workflow:
        """Resumes workflow after payment recovery."""
        workflow_id = wf.workflow_id
        # Step 3: INVENTORY_CHECK
        s3 = self._get_step(db, workflow_id, "INVENTORY_CHECK")
        wf.current_step = "INVENTORY_CHECK"
        s3.status = "RUNNING"
        s3.started_at = datetime.datetime.utcnow()
        db.commit()

        prod_id = metadata.get("product_id", "PROD-LAPTOP-X2")
        inv_res = check_inventory(prod_id)
        if inv_res.available and inv_res.stock_quantity > 0:
            reserve_inventory(prod_id, quantity=metadata.get("quantity", 1))
            s3.status = "SUCCESS"
            s3.completed_at = datetime.datetime.utcnow()
            self._add_audit(db, workflow_id, "INVENTORY_RESERVED", "SYSTEM", f"Stock reserved for '{inv_res.name}'.")
            db.commit()
            return self._complete_confirmation_and_delivery(db, wf, metadata, None)
        else:
            return self._handle_step_failure(db, wf, s3, "OUT_OF_STOCK", "Stock unavailable", metadata)

    def approve_recovery(
        self,
        db: Session,
        approval_id: int,
        approved_by: str = "Senior Operations Manager",
        comments: str = "Approved recovery substitution."
    ) -> Workflow:
        """
        Processes human approval and resumes LangGraph recovery execution.
        """
        appr = db.query(Approval).filter(Approval.id == approval_id).first()
        if not appr:
            raise ValueError(f"Approval with ID {approval_id} not found.")

        appr.approval_status = "APPROVED"
        appr.approved_by = approved_by
        appr.comments = comments
        appr.resolved_at = datetime.datetime.utcnow()

        wf = db.query(Workflow).filter(Workflow.workflow_id == appr.workflow_id).first()
        wf.status = "RECOVERING"
        db.commit()

        self._add_audit(
            db,
            wf.workflow_id,
            "APPROVAL_GRANTED",
            "HUMAN_OPERATOR",
            f"Human Operator '{approved_by}' APPROVED recovery plan: {comments}"
        )

        rec_act = db.query(RecoveryAction).filter(RecoveryAction.id == appr.recovery_action_id).first()
        if rec_act:
            rec_act.status = "APPROVED"
            db.commit()

        # Resume LangGraph execution from execute_action -> verify_recovery
        tool_name = rec_act.tool_name if rec_act else "find_alternative_product"
        params = json.loads(rec_act.parameters_json or "{}") if rec_act else {}
        metadata = json.loads(wf.metadata_json or "{}")

        resume_state = {
            "workflow_id": wf.workflow_id,
            "customer_id": wf.customer_id,
            "current_step": wf.current_step,
            "workflow_status": "RECOVERING",
            "failure_type": "INVENTORY_FAILURE",
            "error_code": "OUT_OF_STOCK",
            "error_message": "Item out of stock",
            "step_id": None,
            "root_cause": appr.reasoning,
            "severity": appr.risk_level,
            "recovery_options": [],
            "recommended_action": appr.proposed_action,
            "recommended_tool": tool_name,
            "tool_parameters": params,
            "ai_reasoning": appr.reasoning,
            "impact_summary": appr.impact_summary,
            "recovery_plan": [],
            "selected_recovery": tool_name,
            "approval_required": True,
            "approval_status": "APPROVED",
            "approval_id": approval_id,
            "approved_by": approved_by,
            "approval_comments": comments,
            "execution_result": {},
            "verification_result": {},
            "is_verified": False,
            "retry_count": 0,
            "max_retries": 3,
            "audit_events": [],
            "metadata": metadata
        }

        # Run execute -> verify nodes
        exec_state = execute_action_node(resume_state)
        resume_state.update(exec_state)

        verify_state = verify_recovery_node(resume_state)
        resume_state.update(verify_state)

        # Log audit events
        for ev in resume_state.get("audit_events", []):
            audit = AuditLog(
                workflow_id=wf.workflow_id,
                event_type=ev.get("event_type", "AGENT_ACTION"),
                actor=ev.get("actor", "AI_AGENT"),
                message=ev.get("message", ""),
                details_json=ev.get("details", "{}"),
                timestamp=datetime.datetime.utcnow()
            )
            db.add(audit)

        if rec_act:
            rec_act.status = "VERIFIED" if resume_state.get("is_verified") else "FAILED"
            rec_act.executed_at = datetime.datetime.utcnow()
            rec_act.result_json = json.dumps(resume_state.get("execution_result", {}))

        # Mark failure resolved
        fail = db.query(Failure).filter(Failure.workflow_id == wf.workflow_id, Failure.status == "ACTIVE").first()
        if fail and resume_state.get("is_verified"):
            fail.status = "RECOVERED"

        # Update step 3
        s3 = self._get_step(db, wf.workflow_id, "INVENTORY_CHECK")
        if s3 and resume_state.get("is_verified"):
            s3.status = "SUCCESS"
            s3.completed_at = datetime.datetime.utcnow()

        db.commit()

        # Advance to step 4 & 5 (Confirmation & Delivery)
        if resume_state.get("is_verified"):
            metadata["force_failure_scenario"] = None
            metadata["product_id"] = "PROD-LAPTOP-X2"  # Substituted product
            wf.metadata_json = json.dumps(metadata)
            db.commit()
            return self._complete_confirmation_and_delivery(db, wf, metadata, None)

        return wf

    def reject_recovery(
        self,
        db: Session,
        approval_id: int,
        rejected_by: str = "Senior Operations Manager",
        comments: str = "Rejected by operations policy."
    ) -> Workflow:
        """Handles rejection of proposed recovery action."""
        appr = db.query(Approval).filter(Approval.id == approval_id).first()
        if not appr:
            raise ValueError(f"Approval with ID {approval_id} not found.")

        appr.approval_status = "REJECTED"
        appr.approved_by = rejected_by
        appr.comments = comments
        appr.resolved_at = datetime.datetime.utcnow()

        wf = db.query(Workflow).filter(Workflow.workflow_id == appr.workflow_id).first()
        wf.status = "CANCELLED"
        db.commit()

        self._add_audit(
            db,
            wf.workflow_id,
            "APPROVAL_REJECTED",
            "HUMAN_OPERATOR",
            f"Human Operator '{rejected_by}' REJECTED recovery plan: {comments}. Order cancelled."
        )

        rec_act = db.query(RecoveryAction).filter(RecoveryAction.id == appr.recovery_action_id).first()
        if rec_act:
            rec_act.status = "REJECTED"

        tools_registry.cancel_order(wf.workflow_id, reason=comments)
        db.commit()
        return wf

    def _get_step(self, db: Session, workflow_id: str, step_name: str) -> WorkflowStep:
        step = db.query(WorkflowStep).filter(
            WorkflowStep.workflow_id == workflow_id,
            WorkflowStep.step_name == step_name
        ).first()
        if not step:
            step = WorkflowStep(workflow_id=workflow_id, step_name=step_name, status="PENDING")
            db.add(step)
            db.commit()
            db.refresh(step)
        return step

    def _add_audit(self, db: Session, workflow_id: str, event_type: str, actor: str, message: str, details: Dict = None):
        audit = AuditLog(
            workflow_id=workflow_id,
            event_type=event_type,
            actor=actor,
            message=message,
            details_json=json.dumps(details or {}),
            timestamp=datetime.datetime.utcnow()
        )
        db.add(audit)
        db.commit()


workflow_engine = WorkflowEngine()
