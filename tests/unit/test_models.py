"""Unit tests for src/myproject/models.py."""

from src.myproject.models import CartItem, CartState


def test_cart_item_defaults():
    """Verify CartItem sets correct default values."""
    item = CartItem(internal_uid="123", item_id="taco_pastor", qty=1)
    assert item.status == "confirmed"
    assert item.tracked_modifiers == []
    assert item.special_instructions == []


def test_cart_state_defaults():
    """Verify CartState initializes correctly."""
    state = CartState(order_id="TEST_001")
    assert state.running_total == 0.0
    assert state.fumbled_state is False
    assert len(state.cart_items) == 0
