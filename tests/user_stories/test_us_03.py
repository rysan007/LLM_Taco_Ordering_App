"""Acceptance test for US-03: System rejects off-menu requests politely."""

import os

import pytest

from src.myproject.state import CartManager
from src.myproject.system2 import BackgroundOrchestrator


@pytest.mark.asyncio
@pytest.mark.user_story("US-03")
async def test_us_03_reject_off_menu():
    """
    Given the application is running,
    When the user orders items not found in the Menu Index (e.g., "Pasta" or "Cheeseburger"),
    Then System 2 formulates a response politely rejecting the items and listing valid taco alternatives, leaving the cart empty.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "dummy_key")
    if api_key == "dummy_key":
        pytest.skip("GEMINI_API_KEY not set. Skipping live LLM test.")

    cm = CartManager()
    sys2 = BackgroundOrchestrator(cart_manager=cm, api_key=api_key)

    turns = [{"role": "user", "text": "Can I get a cheeseburger and a slice of pizza?"}]
    res = await sys2.process_order(turns)

    state = cm.get_state()

    # Assert cart was not polluted
    assert len(state.cart_items) == 0

    # Assert polite rejection and alternatives were provided
    agent_speech = res.get("async_speech", "").lower()
    assert "taco" in agent_speech or "menu" in agent_speech
