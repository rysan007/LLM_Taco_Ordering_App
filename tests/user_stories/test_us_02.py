"""Acceptance test for US-02: HITL Special Request Approval."""

import pytest
from fastapi.testclient import TestClient

from src.myproject.api import app, cart_manager
from src.myproject.models import CartItem


@pytest.mark.user_story("US-02")
def test_us_02_hitl_approval():
    """
    Given the user has ordered an item with a complex modification (e.g., "make the shell extra puffed"),
    When the cook clicks "✓ Approve" in the Kitchen Tablet,
    Then the item's status updates to `confirmed` in the cart, and the agent verbally weaves the approval into the conversation.
    """
    # Isolate state
    cart_manager.clear_state()

    # Inject a pending HITL request into the cart
    test_uid = "hitl_test_001"
    item = CartItem(
        internal_uid=test_uid,
        item_id="taco_puffy_picadillo",
        qty=1,
        special_instructions=["make the shell extra puffed"],
        status="pending_hitl",
    )
    cart_manager.add_or_update_item(item)

    # Trigger the Webhook equivalent of clicking "Approve"
    with TestClient(app) as client:
        response = client.post(
            "/api/kitchen/webhook", json={"internal_uid": test_uid, "approved": True}
        )

    # Validate response and state mutation
    assert response.status_code == 200
    state = cart_manager.get_state()
    assert len(state.cart_items) == 1
    assert state.cart_items[0].status == "confirmed"
