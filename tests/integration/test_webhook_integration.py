"""Integration tests for Neon Trompo backend.

Tests one end-to-end path: HTTP request through API, mutated in CartManager,
and validated via Models.
"""

from fastapi.testclient import TestClient

from src.myproject.api import app, cart_manager
from src.myproject.models import CartItem


def test_webhook_integration_flow():
    """Submitting a kitchen webhook exercises API, CartManager, and Menu pricing."""

    # 1. Seed the State Manager with a pending item
    cart_manager.clear_state()
    pending_item = CartItem(
        internal_uid="hitl_integration_1",
        item_id="taco_pastor",
        qty=1,
        special_instructions=["super spicy"],
        status="pending_hitl",
    )
    cart_manager.add_or_update_item(pending_item)

    # 2. Fire the HTTP Webhook to simulate cook approval
    with TestClient(app) as client:
        response = client.post(
            "/api/kitchen/webhook", json={"internal_uid": "hitl_integration_1", "approved": True}
        )

    # 3. Assert HTTP layer succeeded
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 4. Assert State Manager correctly applied mutations across the system
    state = cart_manager.get_state()
    assert state.cart_items[0].status == "confirmed"

    # 5. Assert Menu Index was accessed to correctly calculate the total
    assert state.running_total == 4.00  # Price of a taco_pastor
