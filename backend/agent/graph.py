import logging
from langgraph.graph import StateGraph, END
from backend.agent.state import RecoveryState
from backend.agent.nodes import (
    monitor_workflow_node,
    detect_failure_node,
    analyze_failure_node,
    create_recovery_plan_node,
    check_approval_required_node,
    execute_action_node,
    verify_recovery_node
)

logger = logging.getLogger("recovery_agent.graph")


def approval_condition(state: RecoveryState) -> str:
    """
    Routes based on human-in-the-loop approval requirement.
    If approval is required and status is PENDING, interrupts graph execution to await human decision.
    """
    if state.get("approval_required") and state.get("approval_status") == "PENDING":
        logger.info(f"[{state['workflow_id']}] Branching: WAITING_FOR_HUMAN_APPROVAL")
        return "wait_for_approval"
    logger.info(f"[{state['workflow_id']}] Branching: Auto-authorized -> EXECUTE_ACTION")
    return "execute_action"


def verification_condition(state: RecoveryState) -> str:
    """
    Routes based on multi-factor business API verification.
    """
    if state.get("is_verified", False):
        logger.info(f"[{state['workflow_id']}] Verification SUCCESS -> Graph COMPLETE")
        return "completed"
    
    retries = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 3)
    if retries < max_retries:
        logger.warning(f"[{state['workflow_id']}] Verification Failed (Retry {retries}/{max_retries}) -> REPLAN")
        return "replan"
    
    logger.error(f"[{state['workflow_id']}] Maximum retries exceeded -> Graph FAILED")
    return "max_retries_exceeded"


def build_recovery_graph():
    """
    Assembles and compiles the LangGraph state machine for autonomous recovery.
    """
    builder = StateGraph(RecoveryState)

    # Register Nodes
    builder.add_node("monitor_workflow", monitor_workflow_node)
    builder.add_node("detect_failure", detect_failure_node)
    builder.add_node("analyze_failure", analyze_failure_node)
    builder.add_node("create_recovery_plan", create_recovery_plan_node)
    builder.add_node("check_approval_required", check_approval_required_node)
    builder.add_node("execute_action", execute_action_node)
    builder.add_node("verify_recovery", verify_recovery_node)

    # Set Entry Point
    builder.set_entry_point("monitor_workflow")

    # Connect Edges
    builder.add_edge("monitor_workflow", "detect_failure")
    builder.add_edge("detect_failure", "analyze_failure")
    builder.add_edge("analyze_failure", "create_recovery_plan")
    builder.add_edge("create_recovery_plan", "check_approval_required")

    # Conditional Branch on Approval
    builder.add_conditional_edges(
        "check_approval_required",
        approval_condition,
        {
            "wait_for_approval": END,
            "execute_action": "execute_action"
        }
    )

    # Execution -> Verification
    builder.add_edge("execute_action", "verify_recovery")

    # Conditional Branch on Verification
    builder.add_conditional_edges(
        "verify_recovery",
        verification_condition,
        {
            "completed": END,
            "replan": "analyze_failure",
            "max_retries_exceeded": END
        }
    )

    return builder.compile()


# Singleton compiled graph instance
recovery_graph = build_recovery_graph()
