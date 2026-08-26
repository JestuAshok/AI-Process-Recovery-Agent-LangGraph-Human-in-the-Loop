import pytest
from backend.business_apis.state import business_state
from backend.business_apis.payment_service import process_payment, get_payment_status
from backend.business_apis.inventory_service import check_inventory, reserve_inventory
from backend.business_apis.order_service import create_order, update_order
from backend.business_apis.delivery_service import schedule_delivery, list_available_carriers
from backend.schemas.schemas import (
    PaymentProcessRequest,
    OrderCreateRequest,
    OrderUpdateRequest,
    DeliveryScheduleRequest
)


def test_payment_success():
    req = PaymentProcessRequest(
        workflow_id="TEST-PAY-01",
        customer_id="CUST-001",
        amount=1299.99
    )
    res = process_payment(req)
    assert res.status == "SUCCESS"
    assert res.amount == 1299.99
    assert res.payment_id.startswith("PAY-")


def test_payment_timeout_simulation():
    req = PaymentProcessRequest(
        workflow_id="TEST-PAY-02",
        customer_id="CUST-001",
        amount=1299.99,
        force_failure="TIMEOUT"
    )
    res = process_payment(req)
    assert res.status == "TIMEOUT"


def test_inventory_check_and_alternatives():
    # Out of stock product
    res = check_inventory("PROD-LAPTOP-X1")
    assert res.available is False
    assert res.stock_quantity == 0
    assert len(res.alternatives) > 0
    # Check that in-stock upgrade alternative is present
    alt = res.alternatives[0]
    assert alt["product_id"] == "PROD-LAPTOP-X2"
    assert alt["available"] is True


def test_order_creation_and_modification():
    ord_req = OrderCreateRequest(
        workflow_id="TEST-ORD-01",
        customer_id="CUST-001",
        items=[{"product_id": "PROD-LAPTOP-X1", "quantity": 1}],
        total_amount=1299.99,
        shipping_address="123 Test St"
    )
    order = create_order(ord_req)
    assert order["workflow_id"] == "TEST-ORD-01"
    assert order["status"] == "CREATED"

    # Modify with replacement SKU
    upd_req = OrderUpdateRequest(
        order_id=order["order_id"],
        replacement_product_id="PROD-LAPTOP-X2"
    )
    updated = update_order(order["order_id"], upd_req)
    assert updated["replaced_from_previous"] is True
    assert updated["active_product_id"] == "PROD-LAPTOP-X2"


def test_delivery_scheduling_and_carrier_switch():
    deliv_req = DeliveryScheduleRequest(
        workflow_id="TEST-DELIV-01",
        order_id="ORD-001",
        carrier="FedEx Express",
        recipient_address="123 Test St"
    )
    res = schedule_delivery(deliv_req)
    assert res.status == "SCHEDULED"
    assert res.tracking_number.startswith("TRK-")
