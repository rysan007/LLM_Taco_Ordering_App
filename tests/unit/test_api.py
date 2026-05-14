"""Unit tests for src/myproject/api.py."""
import os
from fastapi.testclient import TestClient
from src.myproject.api import app, _save_conversation_log

def test_api_health_check():
    """Verify the health endpoint returns 200 OK."""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

def test_api_serve_simulator():
    """Verify the root endpoint serves the HTML UI."""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Neon Trompo" in response.text

def test_api_sdk_endpoint():
    """Verify the Retell SDK proxy endpoint."""
    with TestClient(app) as client:
        response = client.get("/sdk/retell.js")
        assert response.status_code == 200

def test_create_web_call_missing_keys(monkeypatch):
    """Verify web call creation handles missing keys gracefully."""
    monkeypatch.delenv("RETELL_AGENT_ID", raising=False)
    monkeypatch.delenv("RETELL_API_KEY", raising=False)
    with TestClient(app) as client:
        response = client.post("/api/create-web-call")
        assert response.status_code == 200
        assert "error" in response.json()

def test_save_conversation_log():
    """Test the log saving utility execution paths."""
    # Test early return on empty turns
    _save_conversation_log("test_call_123", []) 
    
    # Test successful log creation
    _save_conversation_log("test_call_123", [{"role": "user", "text": "hello"}])
    assert os.path.exists("logs/conversations")

def test_chat_websocket_refresh_and_reset():
    """Verify refresh and reset events in the chat websocket."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws/chat") as ws:
            greeting = ws.receive_json()
            assert greeting["event"] == "response"
            
            # Hit the refresh logic block
            ws.send_json({"event": "refresh", "call_id": "test_1"})
            refresh_res = ws.receive_json()
            assert refresh_res["event"] == "refresh_success"
            
            # Hit the reset logic block
            ws.send_json({"event": "reset", "call_id": "test_1"})
            reset_res = ws.receive_json()
            assert reset_res["event"] == "reset_success"

def test_retell_websocket_ping_pong():
    """Verify ping_pong interactions in the retell websocket."""
    with TestClient(app) as client:
        with client.websocket_connect("/llm-websocket/test_call_123") as ws:
            ws.send_json({"interaction_type": "ping_pong", "timestamp": 12345})
            response = ws.receive_json()
            assert response["interaction_type"] == "ping_pong"
            assert response["timestamp"] == 12345