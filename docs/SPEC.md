# **System Specification: The Neon Trompo Agent**

## **1. Purpose**

The Neon Trompo Voice Agent is a dual-system (System 1 / System 2) AI architecture designed to handle drive-thru ordering. It features ultra-low latency conversational stalling (System 1) paired with a slower, highly accurate background orchestrator (System 2) that manages a strict JSON-based cart state and coordinates Human-in-the-Loop (HITL) kitchen approvals.

## **2. Component Inventory**

The system must be implemented in the following module paths under src/myproject/:

* src/myproject/api.py: The FastAPI application, WebSocket handlers, and Webhook endpoints.  
* src/myproject/models.py: Pydantic data schemas (CartItem, CartState).  
* src/myproject/state.py: The CartManager class for thread-safe state manipulation.  
* src/myproject/menu.py: Static dictionaries for MENU_INDEX and GLOBAL_RULES.  
* src/myproject/system1.py: The ForegroundAgent for fast linguistic intake.  
* src/myproject/system2.py: The BackgroundOrchestrator for deep semantic updates.

## **3. Data Flow**

1. **Intake**: Audio transcript arrives via WebSocket at /ws/chat.  
2. **System 1**: api.py passes text to ForegroundAgent.process_intake(transcript). It returns a fast stall phrase (e.g., "Got it.") which is sent immediately back to the user.  
3. **System 2**: api.py dispatches BackgroundOrchestrator.process_order(turns) asynchronously.  
4. **State Update**: System 2 computes the new cart and calls CartManager.add_or_update_item(item).  
5. **UI Sync**: api.py broadcasts the updated cart and System 2's async speech to the WebSocket.

## **4. Public Interfaces**

### **4.1. Data Models (src/myproject/models.py)**

* **CartItem**: Pydantic model with fields: internal_uid (str), item_id (str), qty (int), tracked_modifiers (list[str], default []), special_instructions (list[str], default []), status (str, default "confirmed").  
* **CartState**: Pydantic model with fields: order_id (str), cart_items (list[CartItem]), running_total (float), fumbled_state (bool).

### **4.2. State Management (src/myproject/state.py)**

* **CartManager**: Class that maintains CartState.  
  * get_state() -> CartState  
  * add_or_update_item(item: CartItem): Replaces item if internal_uid exists, else appends.  
  * update_status(uid: str, approved: bool) -> bool: Changes status of an item. If approved, status becomes "confirmed". If denied, clears special_instructions and keeps status "confirmed".  
  * clear_state()  
  * flag_fumble(status: bool)

### **4.3. Foreground Agent (src/myproject/system1.py)**

* **ForegroundAgent**: Initialized with api_key and cart_manager.  
  * async def process_intake(self, text: str) -> dict: Uses Gemini to return {"intent_type": str, "response_text": str}. If API key is missing/dummy, returns {"intent_type": "standard", "response_text": "Got it."}.

### **4.4. Background Orchestrator (src/myproject/system2.py)**

* **BackgroundOrchestrator**: Initialized with cart_manager and api_key.  
  * async def process_order(self, turns: list) -> dict: Calls Gemini to analyze the conversation. Returns a directives dictionary: {"fumble_detected": bool, "semantic_checkout": "none"|"implicit"|"explicit", "hitl_pending": bool, "async_speech": str}.  
  * Must handle graceful degradation if api_key is "dummy_key" by returning an empty dict {}.

### **4.5. Menu Data (src/myproject/menu.py)**

* **MENU_INDEX**: A dictionary where keys are item IDs (e.g., "taco_pastor") and values are dicts containing name and price.  
* **GLOBAL_RULES**: A dictionary containing rules.

### **4.6. API Endpoints (src/myproject/api.py)**

* app = FastAPI()  
* **@app.get("/")**: Serves simulator.html.  
* **@app.websocket("/ws/chat")**: Accepts websocket. Receives {"event": "text", "transcript": "..."}. Returns {"event": "response", "response_text": "...", "cart_items": [...], "cart_total": 0.0}.  
* **@app.post("/api/kitchen/webhook")**: Accepts JSON payload {"internal_uid": "str", "approved": bool}. Updates CartManager and broadcasts to connected WebSockets.

## **5. Model and Prompt Selection**

* **System 1**: Uses gemini-2.5-flash with a temperature of 0.2 for rapid classification.  
* **System 2**: Uses gemini-2.5-pro with structured JSON schema (response_mime_type="application/json") for rigorous cart state extraction.