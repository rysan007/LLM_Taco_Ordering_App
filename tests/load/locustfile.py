import json
import time

import websocket
from locust import User, between, events, task


class WebSocketUser(User):
    # Simulate users firing requests rapidly
    wait_time = between(0.1, 0.2)

    def on_start(self):
        # Connect to the FastAPI WebSocket when the simulated user spawns
        self.ws = websocket.create_connection("ws://localhost:8000/ws/chat")

    @task
    def send_cached_query(self):
        start_time = time.time()
        try:
            # We explicitly use a generic query so System 2 is NEVER triggered.
            # System 1 will cache this on the very first hit.
            payload = {
                "event": "response_required",
                "call_id": "load_test_sim",
                "transcript": "What are your hours?",
            }
            self.ws.send(json.dumps(payload))
            response = self.ws.recv()

            # Report success to the Locust dashboard/terminal
            events.request.fire(
                request_type="WebSocket",
                name="/ws/chat",
                response_time=int((time.time() - start_time) * 1000),
                response_length=len(response),
                exception=None,
            )
        except Exception as e:
            events.request.fire(
                request_type="WebSocket",
                name="/ws/chat",
                response_time=int((time.time() - start_time) * 1000),
                response_length=0,
                exception=e,
            )

    def on_stop(self):
        self.ws.close()
