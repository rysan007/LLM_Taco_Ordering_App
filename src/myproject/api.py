import asyncio
import json
import os
import random
import urllib.request
from datetime import datetime

import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

from src.myproject.menu import MENU_INDEX
from src.myproject.state import CartManager
from src.myproject.system1 import ForegroundAgent
from src.myproject.system2 import BackgroundOrchestrator

structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ]
)

app = FastAPI(title="Neon Trompo Voice Agent")

cart_manager = CartManager()
api_key = os.environ.get("GEMINI_API_KEY", "dummy_key")

sys1 = ForegroundAgent(api_key=api_key, cart_manager=cart_manager)
sys2 = BackgroundOrchestrator(cart_manager=cart_manager, api_key=api_key)

connected_clients = set()
SDK_CACHE = None


class WebhookPayload(BaseModel):
    internal_uid: str
    approved: bool


def _save_conversation_log(call_id: str, turns: list):
    if not turns:
        return

    os.makedirs("logs/conversations", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_call_id = "".join(c for c in call_id if c.isalnum() or c in "_-")
    filepath = f"logs/conversations/{timestamp}_{safe_call_id}.json"

    state = cart_manager.get_state()
    cart_data = [i.model_dump() for i in state.cart_items]

    data = {"final_total": state.running_total, "final_cart": cart_data, "conversation": turns}

    try:
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        log = structlog.get_logger()
        log.error("failed_to_save_log", error=str(e))


def _build_cart_payload():
    state = cart_manager.get_state()
    rendered_items = []
    for item in state.cart_items:
        menu_info = MENU_INDEX.get(item.item_id, {})
        rendered_items.append(
            {
                "name": menu_info.get("name", item.item_id),
                "qty": item.qty,
                "price": menu_info.get("price", 0.0),
                "status": item.status,
                "uid": item.internal_uid,
                "tracked_modifiers": item.tracked_modifiers,
                "special_instructions": item.special_instructions,
            }
        )
    return {"cart_total": state.running_total, "cart_items": rendered_items}


@app.get("/")
async def serve_simulator():
    with open("src/myproject/simulator.html", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/sdk/retell.js")
async def proxy_retell_sdk():
    global SDK_CACHE
    if SDK_CACHE:
        return Response(content=SDK_CACHE, media_type="application/javascript")

    urls_to_try = [
        "https://esm.sh/retell-client-js-sdk?bundle",
        "https://cdn.jsdelivr.net/npm/retell-client-js-sdk/+esm",
        "https://unpkg.com/retell-client-js-sdk?module",
    ]

    for url in urls_to_try:
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/javascript, */*"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    SDK_CACHE = response.read()
                    return Response(content=SDK_CACHE, media_type="application/javascript")
        except Exception:
            continue
    return Response(
        content="console.error('Failed to fetch SDK.');", media_type="application/javascript"
    )


@app.post("/api/create-web-call")
async def create_web_call():
    agent_id = os.environ.get("RETELL_AGENT_ID")
    retell_key = os.environ.get("RETELL_API_KEY")
    if not agent_id or not retell_key:
        return {"error": "Missing RETELL_AGENT_ID or RETELL_API_KEY in .env"}

    url = "https://api.retellai.com/v2/create-web-call"
    headers = {"Authorization": f"Bearer {retell_key}", "Content-Type": "application/json"}
    data = json.dumps({"agent_id": agent_id}).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as response:
            res_data = json.loads(response.read().decode())
            return {"access_token": res_data.get("access_token")}
    except Exception:
        return {"error": "Failed to create web call"}


@app.websocket("/ws/chat")
async def chat_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    current_sys2_task = None
    turn_history = []
    turn_counter = 0
    call_id = "unknown_call"
    call_state = {"is_active": True, "timeout_stage": 0}

    greeting = "Welcome to The Neon Trompo! Can I take your order?"
    payload = {"event": "response", "response_text": greeting}
    payload.update(_build_cart_payload())
    await websocket.send_json(payload)
    turn_history.append({"role": "agent", "text": greeting})

    try:
        while True:
            try:
                if call_state["is_active"]:
                    data = await asyncio.wait_for(websocket.receive_json(), timeout=15.0)
                    call_state["timeout_stage"] = 0
                else:
                    data = await websocket.receive_json()
            except TimeoutError:
                if call_state["is_active"] and turn_counter > 0:
                    call_state["timeout_stage"] += 1
                    if call_state["timeout_stage"] == 1:
                        timeout_msg = random.choice(
                            [
                                "Is there anything else you'd like to order?",
                                "Anything else for you today?",
                            ]
                        )
                    elif call_state["timeout_stage"] == 2:
                        timeout_msg = "Take your time! Just let me know if you need anything else or if you're ready to check out."
                    else:
                        timeout_msg = (
                            "It seems we've been idle for a bit. I'll pass this call to our staff."
                        )
                        call_state["is_active"] = False
                        _save_conversation_log(call_id, turn_history)

                    turn_history.append({"role": "agent", "text": timeout_msg})
                    out_payload = {"event": "response", "response_text": timeout_msg}
                    out_payload.update(_build_cart_payload())
                    await websocket.send_json(out_payload)
                continue

            call_id = data.get("call_id", call_id)
            log = structlog.get_logger(call_id=call_id)
            event_type = data.get("event")
            transcript = data.get("transcript", "")

            if event_type == "reset":
                _save_conversation_log(call_id, turn_history)
                cart_manager.clear_state()
                sys1._cache.clear()
                if current_sys2_task and not current_sys2_task.done():
                    current_sys2_task.cancel()
                current_sys2_task = None
                turn_history, turn_counter = [], 0
                call_state = {"is_active": True, "timeout_stage": 0}

                payload = {"event": "reset_success", "response_text": greeting}
                payload.update(_build_cart_payload())
                await websocket.send_json(payload)
                turn_history.append({"role": "agent", "text": greeting})
                continue
            elif event_type == "refresh":
                payload = {"event": "refresh_success"}
                payload.update(_build_cart_payload())
                await websocket.send_json(payload)
                continue

            turn_counter += 1
            is_barge_in = False
            if current_sys2_task and not current_sys2_task.done():
                current_sys2_task.cancel()
                is_barge_in = True

            turn_history.append(
                {
                    "role": "user",
                    "turn_id": f"turn_{turn_counter:02d}",
                    "text": transcript,
                    "barge_in": is_barge_in,
                }
            )
            intent_data = await sys1.process_intake(transcript)

            if intent_data.get("intent_type") != "fumbled_speech":
                current_sys2_task = asyncio.create_task(
                    _run_sys2_background(turn_history, websocket, log, call_id, call_state)
                )

            response_text = intent_data.get("response_text", "One moment...")
            out_payload = {"event": "response", "response_text": response_text}
            out_payload.update(_build_cart_payload())
            await websocket.send_json(out_payload)
    except WebSocketDisconnect:
        _save_conversation_log(call_id, turn_history)
    finally:
        connected_clients.discard(websocket)


async def _run_sys2_background(
    turn_history: list, websocket: WebSocket, log, call_id: str, call_state: dict = None
):
    try:
        directives = await sys2.process_order(turn_history)
        payload = _build_cart_payload()
        async_speech = directives.get("async_speech")
        if async_speech:
            if "[TOTAL]" in async_speech:
                async_speech = async_speech.replace(
                    "[TOTAL]", f"${cart_manager.get_state().running_total:.2f}"
                )
            payload["event"], payload["response_text"] = "response", async_speech
            turn_history.append({"role": "agent", "text": async_speech})

        if directives.get("semantic_checkout") == "explicit":
            payload["is_final"] = True
            if call_state is not None:
                call_state["is_active"] = False
            _save_conversation_log(call_id, turn_history)
            if not async_speech:
                fallback = f"Perfect! Your total is ${cart_manager.get_state().running_total:.2f}. We'll have that right out!"
                payload["event"], payload["response_text"] = "response", fallback
                turn_history.append({"role": "agent", "text": fallback})

        for ws in list(connected_clients):
            await ws.send_json(payload)
    except asyncio.CancelledError:
        pass
    except Exception:
        pass


# =====================================================================
# 2. RETELL VOICE ENDPOINT
# =====================================================================
async def _run_sys2_retell_background(
    turn_history: list, websocket: WebSocket, response_id: str, call_id: str, log
):
    try:
        # SOCIAL BUFFER: Give System 1 a head start to finish its stall audio
        # before the "Brain" interjects with the complex answer.
        await asyncio.sleep(1.2)

        directives = await sys2.process_order(turn_history)
        ui_payload = _build_cart_payload()

        async_speech = directives.get("async_speech")
        if async_speech:
            if "[TOTAL]" in async_speech:
                async_speech = async_speech.replace(
                    "[TOTAL]", f"${cart_manager.get_state().running_total:.2f}"
                )

            ui_payload["event"] = "response"
            ui_payload["response_text"] = async_speech

            await websocket.send_json(
                {
                    "response_id": response_id,
                    "content": " " + async_speech,
                    "content_complete": True,
                }
            )
        else:
            await websocket.send_json(
                {"response_id": response_id, "content": "", "content_complete": True}
            )

        if directives and directives.get("semantic_checkout") == "explicit":
            log.info("call_terminated", reason="checkout_complete")
            _save_conversation_log(call_id, turn_history)

        # Broadcast final agent speech and cart to UI
        for ws in list(connected_clients):
            await ws.send_json(ui_payload)

    except asyncio.CancelledError:
        log.info("retell_sys2_task_cancelled")
        pass
    except Exception as e:
        log.error("retell_sys2_task_failed", error=str(e))


@app.websocket("/llm-websocket/{call_id}")
async def retell_voice_endpoint(websocket: WebSocket, call_id: str):
    await websocket.accept()
    log = structlog.get_logger(call_id=call_id)
    log.info("retell_connection_established")
    turn_history = []
    current_sys2_task = None

    try:
        while True:
            data = await websocket.receive_json()
            interaction_type = data.get("interaction_type")

            if interaction_type == "ping_pong":
                await websocket.send_json(
                    {"interaction_type": "ping_pong", "timestamp": data.get("timestamp")}
                )
                continue

            if interaction_type == "response_required":
                response_id = data.get("response_id")

                # Reconstruct history EXACTLY from Retell to prevent duplicates
                transcript_array = data.get("transcript", [])
                turn_history = [{"role": t["role"], "text": t["content"]} for t in transcript_array]

                latest_user_text = ""
                for t in reversed(turn_history):
                    if t["role"] == "user":
                        latest_user_text = t["text"]
                        break

                # SPEAKER BLEED FILTER
                lower_text = latest_user_text.strip().lower()
                if lower_text in [
                    "got it",
                    "got it.",
                    "okay",
                    "okay.",
                    "sure",
                    "sure.",
                    "alright",
                    "alright.",
                    "let me get that.",
                    "one moment.",
                    "added.",
                ]:
                    log.info("speaker_bleed_ignored", text=latest_user_text)
                    await websocket.send_json(
                        {"response_id": response_id, "content": "", "content_complete": True}
                    )
                    continue

                # Barge-in Cancellation
                is_barge_in = False
                if current_sys2_task and not current_sys2_task.done():
                    log.info("barge_in_detected", action="cancelling_stale_task")
                    current_sys2_task.cancel()
                    is_barge_in = True

                # Broadcast clean user text to UI (with barge_in flag)
                for ws in list(connected_clients):
                    await ws.send_json(
                        {
                            "event": "user_transcript",
                            "text": latest_user_text,
                            "is_barge_in": is_barge_in,
                        }
                    )

                intent_data = await sys1.process_intake(latest_user_text)
                stall_text = intent_data.get("response_text", "Just a second...")

                # BROADCAST SYSTEM 1 TO UI
                ui_stall_payload = _build_cart_payload()
                ui_stall_payload["event"] = "response"
                ui_stall_payload["response_text"] = stall_text
                for ws in list(connected_clients):
                    await ws.send_json(ui_stall_payload)

                await websocket.send_json(
                    {"response_id": response_id, "content": stall_text, "content_complete": False}
                )

                current_sys2_task = asyncio.create_task(
                    _run_sys2_retell_background(turn_history, websocket, response_id, call_id, log)
                )
    except WebSocketDisconnect:
        log.info("retell_connection_closed")
        _save_conversation_log(call_id, turn_history)


@app.post("/api/kitchen/webhook")
async def kitchen_webhook(payload: WebhookPayload):
    log = structlog.get_logger(call_id="kitchen_webhook")
    log.info("kitchen_webhook_received", uid=payload.internal_uid, approved=payload.approved)
    success = cart_manager.update_status(payload.internal_uid, payload.approved)
    state = cart_manager.get_state()
    item = next((i for i in state.cart_items if i.internal_uid == payload.internal_uid), None)

    if item:
        menu_info = MENU_INDEX.get(item.item_id, {})
        name = menu_info.get("name", item.item_id)
        request_text = item.special_instructions[0] if item.special_instructions else "that request"
        if not payload.approved:
            item.status = "confirmed"
            item.special_instructions = []
            cart_manager.add_or_update_item(item)
            speech = f"The kitchen just let me know they can't do '{request_text}' for the {name}. I kept the base {name} on your order, is that still okay?"
        else:
            speech = f"Great news, the kitchen said they can do '{request_text}' for your {name}!"

        for ws in list(connected_clients):
            out_payload = {"event": "response", "response_text": speech}
            out_payload.update(_build_cart_payload())
            await ws.send_json(out_payload)

    return {"status": "success" if success else "error"}
