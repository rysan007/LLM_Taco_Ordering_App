"""Unit tests for src/myproject/system1.py."""

import pytest

from src.myproject.state import CartManager
from src.myproject.system1 import ForegroundAgent


@pytest.mark.asyncio
async def test_foreground_agent_initialization_no_key():
    """Verify System 1 handles missing API keys gracefully."""
    cm = CartManager()
    # Provide a dummy key so it skips live Gemini calls
    agent = ForegroundAgent(api_key="dummy_key", cart_manager=cm)

    result = await agent.process_intake("hello")
    assert result["intent_type"] == "unknown"
    assert "GEMINI_API_KEY" in result["response_text"]
