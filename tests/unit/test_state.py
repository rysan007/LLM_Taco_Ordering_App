"""Unit tests for src/myproject/state.py."""

from src.myproject.models import CartItem
from src.myproject.state import CartManager


def test_cart_manager_add_item_and_total():
    """Verify items are added and totals are recalculated accurately."""
    cm = CartManager()

    # Add a $4.00 taco
    item = CartItem(internal_uid="uid1", item_id="taco_pastor", qty=2)
    cm.add_or_update_item(item)

    state = cm.get_state()
    assert len(state.cart_items) == 1
    assert state.running_total == 8.00  # 2 x $4.00


def test_cart_manager_update_status():
    """Verify HITL status updates mutate the item state correctly."""
    cm = CartManager()
    item = CartItem(internal_uid="uid2", item_id="drink_water", qty=1, status="pending_hitl")
    cm.add_or_update_item(item)

    # Approve the item
    success = cm.update_status("uid2", True)
    assert success is True
    assert cm.get_state().cart_items[0].status == "confirmed"

    # Reject a non-existent item
    fail = cm.update_status("uid_fake", False)
    assert fail is False
