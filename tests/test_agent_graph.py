import pytest
from backend.agent.graph import recovery_graph
from backend.agent.tools import tools_registry
from backend.agent.llm import llm_service


def test_agent_tools_execution():
    # Test tool 4: find_alternative_product
    alt = tools_registry.find_alternative_product("PROD-LAPTOP-X1")
    assert alt["success"] is True
    assert alt["alternative_product_id"] == "PROD-LAPTOP-X2"
    assert alt["stock_quantity"] > 0

    # Test tool 2: retry_payment
    pay = tools_registry.retry_payment("WF-TEST-001", "CUST-001", 1299.99)
    assert pay["success"] is True
    assert pay["status"] == "SUCCESS"

    # Test tool 11: verify_inventory
    inv_verif = tools_registry.verify_inventory("PROD-LAPTOP-X2", 1)
    assert inv_verif["verified"] is True


def test_structured_root_cause_analysis():
    wf_data = {"workflow_id": "WF-DEMO-001", "total_amount": 1299.99, "metadata": {"product_id": "PROD-LAPTOP-X1"}}
    fail_data = {"error_code": "OUT_OF_STOCK", "step_name": "INVENTORY_CHECK", "error_message": "0 stock units"}

    rca = llm_service.analyze_failure(wf_data, fail_data)
    assert rca.failure_type == "INVENTORY_FAILURE"
    assert rca.recommended_tool == "find_alternative_product"
    assert rca.approval_required is True
    assert len(rca.recovery_options) > 0


def test_langgraph_recovery_flow_payment_timeout():
    initial_state = {
        "workflow_id": "WF-GRAPH-TEST-01",
        "customer_id": "CUST-001",
        "current_step": "PAYMENT_PROCESSING",
        "workflow_status": "FAILED",
        "failure_type": "PAYMENT_TIMEOUT",
        "error_code": "PAYMENT_GATEWAY_TIMEOUT",
        "error_message": "Gateway timed out",
        "step_id": 2,
        "root_cause": None,
        "severity": "LOW",
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
        "metadata": {"total_amount": 499.50}
    }

    final_state = recovery_graph.invoke(initial_state)
    assert final_state["is_verified"] is True
    assert final_state["workflow_status"] == "COMPLETED"
    assert len(final_state["audit_events"]) >= 4
