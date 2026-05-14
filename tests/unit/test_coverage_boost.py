"""Additional tests to push coverage past the 70% threshold."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from src.myproject.api import app, _run_sys2_background, _run_sys2_retell_background
from src.myproject.system1 import ForegroundAgent
from src.myproject.system2 import BackgroundOrchestrator
from src.myproject.state import CartManager


@pytest.mark.asyncio
async def test_run_sys2_background_explicit():
    """Cover the background task explicit checkout logic in api.py."""
    mock_ws = AsyncMock()
    mock_log = MagicMock()
    call_state = {"is_active": True}
    
    with patch("src.myproject.api.sys2.process_order", new_callable=AsyncMock) as mock_process:
        mock_process.return_value = {"semantic_checkout": "explicit", "async_speech": "[TOTAL]"}
        await _run_sys2_background([{"role": "user", "text": "checkout"}], mock_ws, mock_log, "test_call_bg", call_state)
        # Assert the state correctly deactivated the call
        assert call_state["is_active"] is False


@pytest.mark.asyncio
async def test_run_sys2_retell_background_logic():
    """Cover the retell background task in api.py."""
    mock_ws = AsyncMock()
    mock_log = MagicMock()
    
    with patch("src.myproject.api.sys2.process_order", new_callable=AsyncMock) as mock_process:
        mock_process.return_value = {"semantic_checkout": "explicit", "async_speech": "[TOTAL]"}
        with patch("asyncio.sleep", new_callable=AsyncMock):  # Skip the 1.2s sleep so the test runs instantly
            await _run_sys2_retell_background([{"role": "user", "text": "checkout"}], mock_ws, "res_1", "test_call_retell", mock_log)
            mock_ws.send_json.assert_called()


def test_retell_websocket_speaker_bleed():
    """Cover the speaker bleed ignore block in api.py."""
    with TestClient(app) as client:
        with client.websocket_connect("/llm-websocket/bleed_call") as ws:
            ws.send_json({
                "interaction_type": "response_required",
                "response_id": "bleed_res",
                "transcript": [{"role": "user", "content": "Got it."}]
            })
            res = ws.receive_json()
            assert res["content"] == ""
            assert res["response_id"] == "bleed_res"


@pytest.mark.asyncio
async def test_system1_caching():
    """Cover System 1 cache logic in system1.py."""
    cm = CartManager()
    agent = ForegroundAgent(api_key="fake_key", cart_manager=cm)
    
    with patch.object(agent, "client") as mock_client:
        class MockResponse:
            text = '{"intent_type": "order", "response_text": "cached!"}'
        mock_client.aio.models.generate_content = AsyncMock(return_value=MockResponse())
        
        # First call hits the mock API and caches
        res1 = await agent.process_intake("cache_test")
        # Second call hits the cache dictionary
        res2 = await agent.process_intake("cache_test")
        
        assert mock_client.aio.models.generate_content.call_count == 1
        assert res1 == res2


@pytest.mark.asyncio
async def test_system2_markdown_parsing():
    """Cover the logic that strips markdown code blocks from Gemini's JSON in system2.py."""
    cm = CartManager()
    agent = BackgroundOrchestrator(cart_manager=cm, api_key="fake_key")
    
    with patch.object(agent, "client") as mock_client:
        class MockResponse:
            # Using hex escapes (\x60) for backticks to prevent markdown parser breakage
            text = "\x60\x60\x60json\n{\"directives\": {\"async_speech\": \"markdown test\"}}\n\x60\x60\x60"
        mock_client.aio.models.generate_content = AsyncMock(return_value=MockResponse())
        
        res = await agent.process_order([])
        assert res.get("async_speech") == "markdown test"


@pytest.mark.asyncio
async def test_system2_validation_error():
    """Cover the Pydantic ValidationError catch block in system2.py."""
    cm = CartManager()
    agent = BackgroundOrchestrator(cart_manager=cm, api_key="fake_key")
    
    with patch.object(agent, "client") as mock_client:
        class MockResponse:
            # Missing 'item_id' which is required by CartItem, triggering ValidationError
            text = "{\"updated_cart\": [{\"internal_uid\": \"123\", \"qty\": 1}], \"directives\": {\"fumble_detected\": true}}"
        mock_client.aio.models.generate_content = AsyncMock(return_value=MockResponse())
        
        res = await agent.process_order([])
        assert res.get("fumble_detected") is True