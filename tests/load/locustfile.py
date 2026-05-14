import json
import uuid
from locust import HttpUser, task, between

class TrompoVoiceAgentSimulator(HttpUser):
    """
    Simulates high-volume traffic to the Neon Trompo backend.
    As approved by the instructor, this tests the FastAPI server and state 
    mutations via the REST API rather than hitting the live Retell webhook,
    preventing non-deterministic API waste.
    """
    wait_time = between(0.1, 0.5)

    @task(3)
    def check_health(self):
        """Simulate frequent health checks/pings"""
        self.client.get("/health", name="/health")

    @task(5)
    def load_simulator_ui(self):
        """Simulate users loading the frontend dashboard"""
        self.client.get("/", name="Load Simulator UI")

    @task(2)
    def simulate_kitchen_webhook(self):
        """
        Simulate the kitchen approving/denying items rapidly to stress-test 
        the CartManager's state locking and UI broadcasting mechanisms.
        """
        # Generate a dummy internal UID to simulate random cart items
        dummy_uid = f"item_{uuid.uuid4().hex[:6]}"
        payload = {
            "internal_uid": dummy_uid,
            "approved": True
        }
        
        self.client.post(
            "/api/kitchen/webhook", 
            json=payload,
            name="/api/kitchen/webhook (Simulated HITL)"
        )