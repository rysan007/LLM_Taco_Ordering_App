"""Acceptance test for US-01: User orders standard items and receives immediate stall feedback.

The docstring of every user story test must contain the Given/When/Then from
docs/STORIES.md verbatim. The grading script reads test reports by story ID.
"""

import os

import pytest

from src.myproject.state import CartManager
from src.myproject.system1 import ForegroundAgent
from src.myproject.system2 import BackgroundOrchestrator


@pytest.mark.asyncio
@pytest.mark.user_story("US-01")
async def test_us_01_order_standard_item():
    """
    Given the application is running and connected via Voice,
    When the user says "I want a Neon Pastor taco",
    Then System 1 immediately outputs a short stall phrase (e.g., "One pastor taco...") to the UI,
    and System 2 subsequently adds 1x `taco_pastor` to the Active Cart.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "dummy_key")
    if api_key == "dummy_key":
        pytest.skip("GEMINI_API_KEY not set. Skipping live LLM test.")

    cm = CartManager()
    sys1 = ForegroundAgent(api_key=api_key, cart_manager=cm)
    sys2 = BackgroundOrchestrator(cart_manager=cm, api_key=api_key)

    transcript = "I want a Neon Pastor taco"

    # Verify System 1 catches the intent quickly
    sys1_res = await sys1.process_intake(transcript)
    assert sys1_res.get("intent_type") in ["order", "generic_query"]
    assert len(sys1_res.get("response_text", "")) > 0

    # Verify System 2 updates the cart JSON reliably
    turns = [{"role": "user", "text": transcript}]
    await sys2.process_order(turns)

    state = cm.get_state()
    assert len(state.cart_items) == 1
    assert state.cart_items[0].item_id == "taco_pastor"
