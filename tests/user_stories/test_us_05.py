"""Acceptance test for US-05: Explicit Semantic Checkout with read-back."""

import os

import pytest

from src.myproject.models import CartItem
from src.myproject.state import CartManager
from src.myproject.system2 import BackgroundOrchestrator


@pytest.mark.asyncio
@pytest.mark.user_story("US-05")
async def test_us_05_semantic_checkout():
    """
    Given the user has items in their cart,
    When the user says "That will be all",
    Then System 2 reads back the entire list of items without giving a price (Implicit Checkout).
    And When the user confirms ("That's correct"), Then System 2 gives the final total and finalizes the call (Explicit Checkout).
    """
    api_key = os.environ.get("GEMINI_API_KEY", "dummy_key")
    if api_key == "dummy_key":
        pytest.skip("GEMINI_API_KEY not set. Skipping live LLM test.")

    cm = CartManager()

    # Prep the cart with active items
    cm.add_or_update_item(CartItem(internal_uid="chk_1", item_id="taco_pastor", qty=1))
    cm.add_or_update_item(CartItem(internal_uid="chk_2", item_id="drink_big_red", qty=1))

    sys2 = BackgroundOrchestrator(cart_manager=cm, api_key=api_key)

    # Phase 1: Implicit Checkout (Intent to close, wait for read-back)
    turns = [{"role": "user", "text": "That will be all"}]
    res1 = await sys2.process_order(turns)

    assert res1.get("semantic_checkout") == "implicit"
    agent_reply = res1.get("async_speech", "")

    # Phase 2: Explicit Checkout (Confirmation, expecting total)
    turns.append({"role": "agent", "text": agent_reply})
    turns.append({"role": "user", "text": "That's correct"})

    res2 = await sys2.process_order(turns)
    assert res2.get("semantic_checkout") == "explicit"
    assert "[TOTAL]" in res2.get("async_speech", "")
