"""Acceptance test for US-04: Kitchen denies a Human-in-the-Loop (HITL) request."""

import pytest
from fastapi.testclient import TestClient

from src.myproject.api import app, cart_manager
from src.myproject.models import CartItem


@pytest.mark.user_story("US-04")
def test_us_04_hitl_denial():
    """
    Given the user has ordered an item with a complex modification,
    When the cook clicks "✗ Deny" in the Kitchen Tablet,
    Then the item's status updates to `confirmed` (for the base item), the special instructions are cleared, and the agent verbally informs the user of the rejection.
    """
    # Isolate state
    cart_manager.clear_state()

    # Inject a pending HITL request
    test_uid = "hitl_test_002"
    item = CartItem(
        internal_uid=test_uid,
        item_id="taco_pastor",
        qty=1,
        special_instructions=["put a fried egg on it"],
        status="pending_hitl",
    )
    cart_manager.add_or_update_item(item)

    # Trigger the Webhook equivalent of clicking "Deny"
    with TestClient(app) as client:
        response = client.post(
            "/api/kitchen/webhook", json={"internal_uid": test_uid, "approved": False}
        )

    # Validate state mutation (Item falls back to 'confirmed' but drops instructions)
    assert response.status_code == 200
    state = cart_manager.get_state()
    assert len(state.cart_items) == 1
    assert state.cart_items[0].status == "confirmed"
    assert len(state.cart_items[0].special_instructions) == 0
