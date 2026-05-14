"""Unit tests for src/myproject/system2.py."""
import pytest
from unittest.mock import AsyncMock, patch
from src.myproject.system2 import BackgroundOrchestrator
from src.myproject.state import CartManager

@pytest.mark.asyncio
async def test_background_orchestrator_no_key():
    """Verify System 2 gracefully aborts without an API key."""
    cm = CartManager()
    agent = BackgroundOrchestrator(cart_manager=cm, api_key="dummy_key")
    
    turns = [{"role": "user", "text": "I want a taco"}]
    result = await agent.process_order(turns)
    assert result == {}

@pytest.mark.asyncio
async def test_system2_fallback_logic():
    """Verify System 2 catches exceptions, retries, and returns the anti-silence fallback."""
    cm = CartManager()
    agent = BackgroundOrchestrator(cart_manager=cm, api_key="fake_key_123")
    
    # Mock the client to simulate a Google 503 Outage
    with patch.object(agent, "client") as mock_client:
        mock_client.aio.models.generate_content = AsyncMock(side_effect=Exception("Simulated API 503 Error"))
        
        # Patch asyncio.sleep so the test runs instantly instead of waiting 15 seconds!
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            turns = [{"role": "user", "text": "checkout please"}]
            res = await agent.process_order(turns)
            
            # Assert it hit the final anti-silence fallback
            assert "trouble connecting" in res.get("async_speech", "")
            # Assert it looped through exactly 4 retries
            assert mock_sleep.call_count == 4