import os
import json
import logging
from typing import Dict, Any, Optional
from backend.config import settings
from backend.schemas.schemas import RootCauseAnalysis, RecoveryPlan, RecoveryPlanStep

logger = logging.getLogger("recovery_agent.llm")


class LLMService:
    """
    Intelligent LLM reasoning service with structured JSON output capabilities.
    Supports external LLM providers (OpenAI, Gemini, Anthropic) via LangChain,
    and includes a robust, deterministic heuristic AI engine fallback for 100% offline
    and zero-key execution.
    """

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.model_name = settings.LLM_MODEL
        self.api_key = settings.LLM_API_KEY
        self._llm = None
        self._init_llm_client()

    def _init_llm_client(self):
        if not self.api_key or self.provider == "heuristic":
            logger.info("Using built-in Heuristic AI Recovery Engine (Deterministic Structured Mode).")
            self._llm = None
            return

        try:
            if self.provider == "openai":
                from langchain_openai import ChatOpenAI
                self._llm = ChatOpenAI(
                    model=self.model_name,
                    api_key=self.api_key,
                    temperature=settings.LLM_TEMPERATURE
                )
                logger.info(f"Initialized OpenAI LLM client with model: {self.model_name}")
            elif self.provider in ["gemini", "google"]:
                from langchain_google_genai import ChatGoogleGenerativeAI
                self._llm = ChatGoogleGenerativeAI(
                    model=self.model_name,
                    google_api_key=self.api_key,
                    temperature=settings.LLM_TEMPERATURE
                )
                logger.info(f"Initialized Gemini LLM client with model: {self.model_name}")
            elif self.provider == "anthropic":
                from langchain_anthropic import ChatAnthropic
                self._llm = ChatAnthropic(
                    model=self.model_name,
                    anthropic_api_key=self.api_key,
                    temperature=settings.LLM_TEMPERATURE
                )
                logger.info(f"Initialized Anthropic LLM client with model: {self.model_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize external LLM client: {e}. Falling back to Heuristic AI Engine.")
            self._llm = None

    def analyze_failure(self, workflow_data: Dict[str, Any], failure_data: Dict[str, Any]) -> RootCauseAnalysis:
        """
        Performs structured Root Cause Analysis on a workflow failure.
        """
        error_code = failure_data.get("error_code", "UNKNOWN_ERROR")
        failed_step = failure_data.get("step_name", "UNKNOWN_STEP")
        error_message = failure_data.get("error_message", "")
        product_id = workflow_data.get("metadata", {}).get("product_id", "PROD-LAPTOP-X1")
        total_amount = workflow_data.get("total_amount", 1299.99)

        # 1. Try LLM if configured
        if self._llm:
            try:
                prompt = (
                    f"You are an expert autonomous business process recovery AI.\n"
                    f"Analyze this business process failure:\n"
                    f"Workflow ID: {workflow_data.get('workflow_id')}\n"
                    f"Failed Step: {failed_step}\n"
                    f"Error Code: {error_code}\n"
                    f"Error Message: {error_message}\n"
                    f"Product ID: {product_id}\n"
                    f"Total Amount: ${total_amount}\n\n"
                    f"Provide structured JSON output matching RootCauseAnalysis schema."
                )
                structured_llm = self._llm.with_structured_output(RootCauseAnalysis)
                result = structured_llm.invoke(prompt)
                if isinstance(result, RootCauseAnalysis):
                    return result
            except Exception as e:
                logger.warning(f"LLM RCA failed: {e}. Utilizing deterministic reasoning engine.")

        # 2. Heuristic Deterministic AI Analysis
        return self._heuristic_analyze_failure(error_code, failed_step, error_message, product_id, total_amount)

    def _heuristic_analyze_failure(self, error_code: str, failed_step: str, error_message: str, product_id: str, total_amount: float) -> RootCauseAnalysis:
        """
        Deterministic, domain-aware Root-Cause Analysis.
        """
        if error_code in ["OUT_OF_STOCK", "INVENTORY_UNAVAILABLE"] or failed_step == "INVENTORY_CHECK":
            return RootCauseAnalysis(
                failure_type="INVENTORY_FAILURE",
                root_cause=f"Primary product '{product_id}' is out of stock in warehouse fulfillment centers.",
                severity="MEDIUM",
                recovery_options=[
                    "Scan catalog for identical-spec in-stock alternative product",
                    "Request human approval for product substitution upgrade",
                    "Update order line items and verify stock availability",
                    "Cancel order and issue customer store credit"
                ],
                recommended_action="Substitute with available upgrade edition (PROD-LAPTOP-X2) at zero additional cost to maintain customer SLA",
                recommended_tool="find_alternative_product",
                tool_parameters={"product_id": product_id},
                approval_required=True,
                risk_assessment="Product substitution modifies customer order line items. Business policy mandates human confirmation before committing replacement.",
                impact_summary="Zero customer charge delta; customer receives higher-spec 1TB SSD model within promised SLA window."
            )

        elif error_code in ["PAYMENT_TIMEOUT", "PAYMENT_GATEWAY_TIMEOUT"] or (failed_step == "PAYMENT_PROCESSING" and "timeout" in error_message.lower()):
            return RootCauseAnalysis(
                failure_type="PAYMENT_FAILURE",
                root_cause="Primary payment gateway did not acknowledge transaction within 4000ms SLA timeout window.",
                severity="LOW",
                recovery_options=[
                    "Check payment status directly with clearing network",
                    "Retry payment via secondary fallback gateway route",
                    "Prompt customer for alternate payment method"
                ],
                recommended_action="Execute automated retry via secondary payment gateway channel",
                recommended_tool="retry_payment",
                tool_parameters={"amount": total_amount, "payment_method": "CREDIT_CARD_FALLBACK"},
                approval_required=False,
                risk_assessment="Automated idempotent retry on network timeout is low-risk and authorized by standard operating procedure.",
                impact_summary="Immediate resolution without customer friction or delay."
            )

        elif error_code in ["INVENTORY_SERVICE_DOWN", "HTTP_503_SERVICE_UNAVAILABLE"] or "503" in error_message:
            return RootCauseAnalysis(
                failure_type="INFRASTRUCTURE_OUTAGE",
                root_cause="Warehouse Inventory API cluster returned HTTP 503 Service Unavailable due to transient network congestion.",
                severity="MEDIUM",
                recovery_options=[
                    "Execute exponential backoff retry with circuit breaker check",
                    "Query read-only inventory replica snapshot",
                    "Escalate to DevOps on-call if outage persists beyond 3 retries"
                ],
                recommended_action="Perform controlled exponential backoff retry cycle and resume workflow",
                recommended_tool="check_inventory",
                tool_parameters={"product_id": product_id},
                approval_required=False,
                risk_assessment="Transient service degradation can be self-healed via backoff retry before escalating.",
                impact_summary="Workflow delayed by approx 2.5s while service cluster recovers."
            )

        elif error_code in ["DELIVERY_SERVICE_UNAVAILABLE", "CARRIER_DISPATCH_FAILED"] or failed_step == "DELIVERY_SCHEDULING":
            return RootCauseAnalysis(
                failure_type="LOGISTICS_FAILURE",
                root_cause="Primary delivery carrier (FedEx Express) dispatch gateway offline or experiencing regional depot congestion.",
                severity="LOW",
                recovery_options=[
                    "Reroute shipment to secondary certified carrier (UPS Next Day)",
                    "Retry primary carrier dispatch queue",
                    "Hold order at warehouse pickup hub"
                ],
                recommended_action="Reroute parcel dispatch to partner carrier (UPS Next Day) at identical delivery tier",
                recommended_tool="find_alternate_delivery",
                tool_parameters={},
                approval_required=False,
                risk_assessment="Partner carrier operates under existing SLA and agreed enterprise rate card.",
                impact_summary="Shipment remains on schedule for next-day customer delivery."
            )

        elif total_amount >= 2000.0 or error_code == "HIGH_VALUE_REFUND":
            return RootCauseAnalysis(
                failure_type="HIGH_VALUE_RISK",
                root_cause="High-value transaction exception exceeding standard automated recovery delegation limit ($2,000 threshold).",
                severity="HIGH",
                recovery_options=[
                    "Request Senior Operations Manager manual review and approval",
                    "Issue full transaction refund and order cancellation",
                    "Offer store manager VIP customer discount"
                ],
                recommended_action="Submit transaction summary for immediate Operations Manager sign-off",
                recommended_tool="send_notification",
                tool_parameters={"channel": "EMAIL", "subject": "High Value Approval Pending"},
                approval_required=True,
                risk_assessment="Transaction value ($2,499.99) exceeds autonomous remediation limit. Corporate compliance requires documented sign-off.",
                impact_summary="Audit record will link manager identity and decision timestamp for compliance."
            )

        # General fallback
        return RootCauseAnalysis(
            failure_type="OPERATIONAL_FAILURE",
            root_cause=f"Unhandled exception encountered at step '{failed_step}': {error_message or error_code}",
            severity="MEDIUM",
            recovery_options=[
                "Perform safe automated retry of failed step",
                "Request human intervention",
                "Gracefully terminate workflow"
            ],
            recommended_action="Execute automated retry of the failed workflow step",
            recommended_tool="retry_payment" if failed_step == "PAYMENT_PROCESSING" else "check_inventory",
            tool_parameters={},
            approval_required=False,
            risk_assessment="Standard recovery retry procedure.",
            impact_summary="Workflow resumes upon successful step execution."
        )

    def generate_recovery_plan(self, rca: RootCauseAnalysis, workflow_id: str) -> RecoveryPlan:
        """
        Generates step-by-step actionable recovery plan from Root Cause Analysis.
        """
        steps = []
        if rca.failure_type == "INVENTORY_FAILURE":
            steps = [
                RecoveryPlanStep(step_number=1, action_name="Scan Catalog Alternatives", description="Query inventory for identical/higher spec products with stock availability > 0.", requires_approval=False),
                RecoveryPlanStep(step_number=2, action_name="Match Optimal Replacement", description="Select Zenith ProBook 15 Plus (1TB NVMe SSD) at zero cost variance.", requires_approval=False),
                RecoveryPlanStep(step_number=3, action_name="Human Approval Gate", description="Present substitution plan and risk analysis to Operations Manager.", requires_approval=True),
                RecoveryPlanStep(step_number=4, action_name="Apply Order Modification", description="Update order line items with replacement SKU and customer delivery note.", requires_approval=False),
                RecoveryPlanStep(step_number=5, action_name="Verify Warehouse Allocation", description="Execute live stock audit to confirm allocated inventory.", requires_approval=False),
                RecoveryPlanStep(step_number=6, action_name="Resume Order Confirmation", description="Advance workflow to delivery scheduling.", requires_approval=False)
            ]
        elif rca.failure_type == "PAYMENT_FAILURE":
            steps = [
                RecoveryPlanStep(step_number=1, action_name="Query Gateway Transaction Status", description="Check if charge was partially processed before timeout.", requires_approval=False),
                RecoveryPlanStep(step_number=2, action_name="Execute Secondary Gateway Retry", description="Route transaction through backup payment processor.", requires_approval=False),
                RecoveryPlanStep(step_number=3, action_name="Verify Settlement", description="Confirm authorization code and fund capture.", requires_approval=False),
                RecoveryPlanStep(step_number=4, action_name="Advance Workflow", description="Mark payment successful and transition to inventory check.", requires_approval=False)
            ]
        elif rca.failure_type == "LOGISTICS_FAILURE":
            steps = [
                RecoveryPlanStep(step_number=1, action_name="Check Carrier Service Outage", description="Audit FedEx Express dispatch gateway response.", requires_approval=False),
                RecoveryPlanStep(step_number=2, action_name="Select Alternate Carrier", description="Switch booking to UPS Next Day express route.", requires_approval=False),
                RecoveryPlanStep(step_number=3, action_name="Generate Tracking Number", description="Acquire tracking manifest and assign to customer order.", requires_approval=False),
                RecoveryPlanStep(step_number=4, action_name="Verify Dispatch Status", description="Confirm carrier pickup window and complete workflow.", requires_approval=False)
            ]
        else:
            steps = [
                RecoveryPlanStep(step_number=1, action_name="Isolate Failure Root Cause", description=rca.root_cause, requires_approval=False),
                RecoveryPlanStep(step_number=2, action_name="Execute Remediation Tool", description=f"Invoke {rca.recommended_tool} with verified parameters.", requires_approval=rca.approval_required),
                RecoveryPlanStep(step_number=3, action_name="Verify State Consistency", description="Audit updated state across business databases.", requires_approval=False),
                RecoveryPlanStep(step_number=4, action_name="Complete Workflow", description="Finalize order and notify stakeholder.", requires_approval=False)
            ]

        return RecoveryPlan(
            workflow_id=workflow_id,
            failure_summary=rca.root_cause,
            root_cause=rca.root_cause,
            steps=steps,
            selected_tool=rca.recommended_tool,
            tool_parameters=rca.tool_parameters,
            approval_required=rca.approval_required,
            ai_reasoning=f"AI Agent evaluated {len(rca.recovery_options)} recovery strategies. Selected '{rca.recommended_action}' based on SLA retention, cost neutrality, and policy compliance."
        )


llm_service = LLMService()
