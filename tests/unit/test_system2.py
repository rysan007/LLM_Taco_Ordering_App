"""Unit tests for src/myproject/system2.py."""

import pytest

from src.myproject.state import CartManager
from src.myproject.system2 import BackgroundOrchestrator


@pytest.mark.asyncio
async def test_background_orchestrator_no_key():
    """Verify System 2 gracefully aborts without an API key."""
    cm = CartManager()
    # Provide a dummy key so it skips live Gemini calls
    agent = BackgroundOrchestrator(cart_manager=cm, api_key="dummy_key")

    turns = [{"role": "user", "text": "I want a taco"}]
    result = await agent.process_order(turns)

    # Without a client, it should return an empty dict
    assert result == {}
