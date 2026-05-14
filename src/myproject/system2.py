import asyncio
import json

import structlog
from google import genai
from google.genai import types

from src.myproject.menu import GLOBAL_RULES, MENU_INDEX
from src.myproject.models import CartItem
from src.myproject.state import CartManager


class BackgroundOrchestrator:
    def __init__(self, cart_manager: CartManager, api_key: str) -> None:
        self.cart_manager = cart_manager
        self.api_key = api_key
        self.client = genai.Client(api_key=self.api_key) if api_key != "dummy_key" else None
        self.log = structlog.get_logger()

    async def process_order(self, turns: list) -> dict:
        if not self.client:
            return {}

        current_state = self.cart_manager.get_state()
        cart_json_str = json.dumps([i.model_dump() for i in current_state.cart_items])

        lite_menu = {
            k: {
                "name": v["name"],
                "description": v.get("description", ""),
                "dietary_info": v.get("dietary_info", {}),
                "default_ingredients": v.get("default_ingredients", []),
                "allowed_modifications": v.get("allowed_modifications", []),
                "upsell_target": v.get("upsell_target"),
            }
            for k, v in MENU_INDEX.items()
        }

        system_instruction = f"""You are System 2, the Background Brain for The Neon Trompo.
You receive a structured sequence of Conversation Turns (User and Agent roles) and the current Cart JSON. You make ALL logical decisions.

RULES FOR ASYNC SPEECH (SINGLE STRING OUTPUT):
1. REJECTIONS & AMBIGUITY: Handle off-menu or generic requests politely.
2. QUERIES: Answer questions using default_ingredients and description.
3. ORDER REVIEW (IMPLICIT CHECKOUT): If the user indicates they are done ordering (e.g., "that will be all"), DO NOT finalize the call immediately. Set `semantic_checkout` to `implicit`. Read back their ENTIRE current order (including modifiers and special instructions) and ask for confirmation (e.g., "Got it. So you have [items]. Does that look right?"). DO NOT give the total price yet.
4. ORDER FINALIZATION (EXPLICIT CHECKOUT): Critically analyze the Turn History. IF the last thing the agent said was an Order Review (e.g., "Does that look right?") AND the user's latest response is an agreement (e.g., "yes", "looks good", "that's correct"), YOU MUST set `semantic_checkout` to `explicit`. You MUST set `async_speech` to explicitly state the final total using the exact string "[TOTAL]".
5. MOMENTUM: Always provide a momentum phrase unless explicitly checking out.
6. KITCHEN APPROVALS & WEAVING (CRITICAL):
   - Status "pending_hitl" = Still waiting. DO NOT bring this up unprompted. Only mention you are still waiting if the user explicitly asks.
   - Status "confirmed" (on an item with special_instructions) = KITCHEN APPROVED.
   - Read the Turn History: If an item is 'confirmed' but the Agent hasn't verbally announced the approval yet, you MUST announce it now.
   - WEAVE YOUR SPEECH: If you need to announce an approval AND acknowledge a new item, weave them together smoothly. (e.g., "Great news, the kitchen approved your extra crispy shell! I've also added your Big Red. What else sounds good?").
7. STT STUMBLES: Do not double-count items already in the cart.

Menu Index Reference: {json.dumps(lite_menu)}
Global Rules: {GLOBAL_RULES['system_warning']}

You MUST output valid JSON only:
{{
    "updated_cart": [ {{ "internal_uid": "str", "item_id": "str", "qty": 1, "tracked_modifiers": ["str"], "special_instructions": ["str"], "status": "confirmed" | "pending_hitl" }} ],
    "directives": {{
        "fumble_detected": false,
        "semantic_checkout": "none" | "implicit" | "explicit",
        "hitl_pending": false,
        "async_speech": "string"
    }}
}}"""

        prompt = f"""
Current Cart Items: {cart_json_str}
Conversation History: {json.dumps(turns, indent=2)}

Analyze the history and cart. Return the JSON.
"""
        delays = [1, 2, 4, 8, 16]
        for attempt in range(6):
            try:
                response = await self.client.aio.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.0,
                    ),
                )

                output = json.loads(response.text)
                self.log.info("sys2_llm_raw_output", llm_json=output)

                updated_items_data = output.get("updated_cart", [])
                directives = output.get("directives", {})

                true_current_state = self.cart_manager.get_state()
                true_items_map = {i.internal_uid: i for i in true_current_state.cart_items}

                self.cart_manager.clear_state()
                self.cart_manager.flag_fumble(directives.get("fumble_detected", False))
                self.cart_manager.latest_directives = directives

                for item_data in updated_items_data:
                    uid = item_data.get("internal_uid")
                    # STRICT STATE LOCK: Preserve 'confirmed' status from webhooks
                    if uid in true_items_map:
                        existing_item = true_items_map[uid]
                        if existing_item.status == "confirmed":
                            item_data["status"] = "confirmed"

                    item = CartItem(**item_data)
                    self.cart_manager.add_or_update_item(item)

                return directives
            except Exception:
                if attempt < 5:
                    await asyncio.sleep(delays[attempt])
                else:
                    return {}
