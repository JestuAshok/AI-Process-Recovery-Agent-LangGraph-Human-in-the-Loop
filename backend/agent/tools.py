import json
import time
from typing import Dict, Any, Optional
from backend.business_apis.state import business_state


class AgentTools:
    """
    Controlled tool suite for the AI Recovery Agent.
    The LLM never runs arbitrary shell or raw API code; it selects and invokes
    these predefined, verified business recovery tools.
    """

    @staticmethod
    def check_payment_status(workflow_id: str, payment_id: Optional[str] = None) -> Dict[str, Any]:
        """Tool 1: Verifies the true status of a payment transaction from the payment processor."""
        for pid, data in business_state.payments.items():
            if data.get("workflow_id") == workflow_id or pid == payment_id:
                return {
                    "success": True,
                    "payment_id": pid,
                    "status": data.get("status"),
                    "amount": data.get("amount"),
                    "message": f"Payment status found: {data.get('status')}"
                }
        return {
            "success": False,
            "status": "NOT_FOUND",
            "message": f"No payment record found for workflow {workflow_id}"
        }

    @staticmethod
    def retry_payment(workflow_id: str, customer_id: str, amount: float, payment_method: str = "CREDIT_CARD_FALLBACK") -> Dict[str, Any]:
        """Tool 2: Re-submits payment request using safe fallback gateway channel."""
        # Clear any transient timeout fault for this retry
        if business_state.is_fault_active("payment") == "TIMEOUT":
            business_state.clear_fault("payment")

        payment_id = f"PAY-RETRY-{int(time.time())}"
        record = {
            "payment_id": payment_id,
            "workflow_id": workflow_id,
            "customer_id": customer_id,
            "status": "SUCCESS",
            "amount": amount,
            "currency": "USD",
            "payment_method": payment_method,
            "timestamp": time.time(),
            "retry_success": True
        }
        business_state.payments[payment_id] = record
        business_state.record_metric("payment", success=True, latency=60)
        return {
            "success": True,
            "payment_id": payment_id,
            "status": "SUCCESS",
            "amount": amount,
            "message": "Payment retry executed successfully via secondary gateway."
        }

    @staticmethod
    def check_inventory(product_id: str) -> Dict[str, Any]:
        """Tool 3: Queries warehouse inventory stock and availability."""
        if product_id not in business_state.products:
            return {"success": False, "available": False, "stock": 0, "message": f"Product '{product_id}' not found in catalog."}

        prod = business_state.products[product_id]
        is_avail = prod["stock_quantity"] > 0
        return {
            "success": True,
            "product_id": product_id,
            "name": prod["name"],
            "available": is_avail,
            "stock_quantity": prod["stock_quantity"],
            "unit_price": prod["unit_price"],
            "category": prod["category"],
            "message": f"Product '{prod['name']}' has {prod['stock_quantity']} units in stock."
        }

    @staticmethod
    def find_alternative_product(product_id: str) -> Dict[str, Any]:
        """Tool 4: Scans catalog for in-stock comparable products (specs, price, category match)."""
        if product_id not in business_state.products:
            # Return general in-stock alternative
            for pid, p in business_state.products.items():
                if p["stock_quantity"] > 0:
                    return {
                        "success": True,
                        "original_product_id": product_id,
                        "alternative_product_id": pid,
                        "alternative_name": p["name"],
                        "unit_price": p["unit_price"],
                        "stock_quantity": p["stock_quantity"],
                        "price_difference": 0.0,
                        "specifications": p.get("specifications", {}),
                        "recommendation_score": 0.95
                    }

        orig_prod = business_state.products[product_id]
        alt_ids = orig_prod.get("alternatives", [])
        
        candidates = []
        for aid in alt_ids:
            if aid in business_state.products:
                alt = business_state.products[aid]
                if alt["stock_quantity"] > 0:
                    price_diff = round(alt["unit_price"] - orig_prod["unit_price"], 2)
                    candidates.append({
                        "product_id": aid,
                        "name": alt["name"],
                        "unit_price": alt["unit_price"],
                        "stock_quantity": alt["stock_quantity"],
                        "price_difference": price_diff,
                        "specifications": alt.get("specifications", {}),
                        "recommendation_score": 0.98 if price_diff == 0 else 0.90
                    })

        # If no explicit alternative found, search same category
        if not candidates:
            for pid, p in business_state.products.items():
                if pid != product_id and p.get("category") == orig_prod.get("category") and p["stock_quantity"] > 0:
                    candidates.append({
                        "product_id": pid,
                        "name": p["name"],
                        "unit_price": p["unit_price"],
                        "stock_quantity": p["stock_quantity"],
                        "price_difference": round(p["unit_price"] - orig_prod["unit_price"], 2),
                        "specifications": p.get("specifications", {}),
                        "recommendation_score": 0.85
                    })

        if candidates:
            # Pick highest recommendation score
            best = max(candidates, key=lambda x: x["recommendation_score"])
            return {
                "success": True,
                "original_product_id": product_id,
                "original_product_name": orig_prod["name"],
                "alternative_product_id": best["product_id"],
                "alternative_name": best["name"],
                "unit_price": best["unit_price"],
                "stock_quantity": best["stock_quantity"],
                "price_difference": best["price_difference"],
                "specifications": best["specifications"],
                "all_candidates": candidates,
                "message": f"Found optimal in-stock alternative: {best['name']} (Stock: {best['stock_quantity']})"
            }

        return {
            "success": False,
            "message": f"No in-stock alternatives available for product {product_id}"
        }

    @staticmethod
    def update_order(workflow_id: str, replacement_product_id: Optional[str] = None, new_quantity: Optional[int] = None, new_total_amount: Optional[float] = None) -> Dict[str, Any]:
        """Tool 5: Safely modifies the order with approved alternative products or adjusted totals."""
        target = None
        for oid, data in business_state.orders.items():
            if data.get("workflow_id") == workflow_id:
                target = data
                break

        if not target:
            # Create or mock order record
            oid = f"ORD-{workflow_id[-6:]}"
            target = {
                "order_id": oid,
                "workflow_id": workflow_id,
                "items": [],
                "total_amount": new_total_amount or 1299.99,
                "status": "UPDATED"
            }
            business_state.orders[oid] = target

        if replacement_product_id:
            alt_prod = business_state.products.get(replacement_product_id)
            name = alt_prod["name"] if alt_prod else "Replacement Product"
            price = alt_prod["unit_price"] if alt_prod else target["total_amount"]
            target["items"] = [{
                "product_id": replacement_product_id,
                "name": name,
                "quantity": new_quantity or 1,
                "unit_price": price
            }]
            target["active_product_id"] = replacement_product_id
            target["status"] = "ITEM_REPLACED"

        if new_total_amount is not None:
            target["total_amount"] = new_total_amount

        target["updated_at"] = time.time()
        business_state.record_metric("order", success=True, latency=30)
        return {
            "success": True,
            "order_id": target.get("order_id"),
            "workflow_id": workflow_id,
            "active_product_id": replacement_product_id,
            "items": target.get("items"),
            "status": "ORDER_UPDATED",
            "message": f"Order successfully updated with product {replacement_product_id}."
        }

    @staticmethod
    def cancel_order(workflow_id: str, reason: str = "Unrecoverable workflow error") -> Dict[str, Any]:
        """Tool 6: Gracefully cancels the order and marks customer account for reconciliation."""
        for oid, data in business_state.orders.items():
            if data.get("workflow_id") == workflow_id:
                data["status"] = "CANCELLED"
                data["cancellation_reason"] = reason
                return {"success": True, "order_id": oid, "status": "CANCELLED", "reason": reason}

        return {"success": True, "workflow_id": workflow_id, "status": "CANCELLED", "reason": reason}

    @staticmethod
    def schedule_delivery(workflow_id: str, order_id: str, carrier: str = "FedEx Express", recipient_address: str = "Customer Shipping Address") -> Dict[str, Any]:
        """Tool 7: Books delivery with carrier."""
        tracking_num = f"TRK-{int(time.time())}"
        record = {
            "tracking_number": tracking_num,
            "workflow_id": workflow_id,
            "order_id": order_id,
            "carrier": carrier,
            "status": "SCHEDULED",
            "recipient_address": recipient_address,
            "scheduled_at": time.time()
        }
        business_state.deliveries[tracking_num] = record
        business_state.record_metric("delivery", success=True, latency=45)
        return {
            "success": True,
            "tracking_number": tracking_num,
            "carrier": carrier,
            "status": "SCHEDULED",
            "message": f"Delivery scheduled with {carrier} (Tracking: {tracking_num})"
        }

    @staticmethod
    def find_alternate_delivery(workflow_id: str, recipient_address: str = "Customer Shipping Address") -> Dict[str, Any]:
        """Tool 8: Finds available alternate carrier when primary delivery partner fails."""
        # Find next operational carrier
        selected_carrier = "UPS Next Day"
        tracking_num = f"TRK-ALT-{int(time.time())}"
        record = {
            "tracking_number": tracking_num,
            "workflow_id": workflow_id,
            "order_id": f"ORD-{workflow_id[-6:]}",
            "carrier": selected_carrier,
            "status": "SCHEDULED",
            "recipient_address": recipient_address,
            "scheduled_at": time.time(),
            "rerouted": True
        }
        business_state.deliveries[tracking_num] = record
        business_state.record_metric("delivery", success=True, latency=40)
        return {
            "success": True,
            "carrier": selected_carrier,
            "tracking_number": tracking_num,
            "status": "SCHEDULED",
            "message": f"Rerouted delivery to {selected_carrier}. Dispatch confirmed."
        }

    @staticmethod
    def send_notification(workflow_id: str, recipient: str, channel: str, subject: str, content: str) -> Dict[str, Any]:
        """Tool 9: Sends status update notification to customer."""
        notif_id = f"NOTIF-{int(time.time())}"
        business_state.notifications.append({
            "notification_id": notif_id,
            "workflow_id": workflow_id,
            "recipient": recipient,
            "channel": channel,
            "subject": subject,
            "content": content,
            "sent_at": time.time()
        })
        return {
            "success": True,
            "notification_id": notif_id,
            "channel": channel,
            "message": f"Notification '{subject}' dispatched via {channel}."
        }

    @staticmethod
    def verify_payment(workflow_id: str) -> Dict[str, Any]:
        """Tool 10: Multi-factor verification of captured funds."""
        success_found = None
        for pid, data in business_state.payments.items():
            if data.get("workflow_id") == workflow_id:
                if data.get("status") in ["SUCCESS", "CAPTURED"]:
                    success_found = data
                    break

        if success_found:
            return {
                "verified": True,
                "payment_id": success_found.get("payment_id"),
                "status": success_found.get("status"),
                "amount": success_found.get("amount"),
                "details": "Payment captured and confirmed by banking gateway."
            }

        return {"verified": False, "status": "UNKNOWN", "details": "No authorized payment record verified."}

    @staticmethod
    def verify_inventory(product_id: str, required_qty: int = 1) -> Dict[str, Any]:
        """Tool 11: Direct warehouse stock audit verification."""
        if product_id not in business_state.products:
            return {"verified": False, "product_id": product_id, "details": "Product not found"}

        prod = business_state.products[product_id]
        is_ok = prod["stock_quantity"] >= required_qty
        return {
            "verified": is_ok,
            "product_id": product_id,
            "name": prod["name"],
            "stock_quantity": prod["stock_quantity"],
            "details": f"Stock verified: {prod['stock_quantity']} units on shelf for {prod['name']}." if is_ok else "Insufficient stock."
        }

    @staticmethod
    def verify_order(workflow_id: str) -> Dict[str, Any]:
        """Tool 12: End-to-end consistency audit for order items and pricing."""
        for oid, data in business_state.orders.items():
            if data.get("workflow_id") == workflow_id:
                has_items = len(data.get("items", [])) > 0
                is_valid = data.get("status") not in ["CANCELLED", "FAILED"] and has_items
                return {
                    "verified": is_valid,
                    "order_id": oid,
                    "status": data.get("status"),
                    "item_count": len(data.get("items", [])),
                    "total_amount": data.get("total_amount"),
                    "details": "Order payload is consistent and valid." if is_valid else "Order is cancelled or empty."
                }
        return {"verified": False, "details": "Order record not found."}


tools_registry = AgentTools()
