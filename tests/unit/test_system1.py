"""Unit tests for src/myproject/system1.py."""
import pytest
from unittest.mock import AsyncMock, patch
from src.myproject.system1 import ForegroundAgent
from src.myproject.state import CartManager
from src.myproject.models import CartState

@pytest.mark.asyncio
async def test_foreground_agent_initialization_no_key():
    """Verify System 1 handles missing API keys gracefully."""
    cm = CartManager()
    agent = ForegroundAgent(api_key="dummy_key", cart_manager=cm)
    
    result = await agent.process_intake("hello")
    assert result["intent_type"] == "unknown"
    assert "GEMINI_API_KEY" in result["response_text"]

@pytest.mark.asyncio
async def test_system1_exception_fallback():
    """Verify System 1 catches exceptions and returns the safe fallback phrase."""
    cm = CartManager()
    agent = ForegroundAgent(api_key="fake_key_123", cart_manager=cm)
    
    # Mock the client to throw an exception, forcing the except block to run
    with patch.object(agent, "client") as mock_client:
        mock_client.aio.models.generate_content = AsyncMock(side_effect=Exception("API Error"))
        res = await agent.process_intake("hello")
        assert res["intent_type"] == "fumbled_speech"
        assert "missed that" in res["response_text"]

@pytest.mark.asyncio
async def test_system1_generate_response():
    """Verify generate_response produces the total string."""
    agent = ForegroundAgent(api_key="dummy_key")
    state = CartState(order_id="1", running_total=12.50)
    res = await agent.generate_response(state, [])
    assert "12.50" in res