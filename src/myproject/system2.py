import asyncio
import json
import time

import structlog
from google import genai
from google.genai import types
from pydantic import ValidationError

from .menu import GLOBAL_RULES, MENU_INDEX
from .models import CartItem


class BackgroundOrchestrator:
    def __init__(self, cart_manager, api_key: str):
        self.cart_manager = cart_manager
        self.api_key = api_key
        self.log = structlog.get_logger()
        if self.api_key and self.api_key != "dummy_key":
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    async def process_order(self, turns: list) -> dict:
        if not self.client or self.api_key == "dummy_key":
            self.log.warning("sys2_aborted_no_api_key")
            return {}

        self.log.info("sys2_process_order_started", turns_count=len(turns))

        # 1. Prepare Cart
        current_cart = self.cart_manager.get_state().model_dump()

        # 2. Prepare History
        history_text = json.dumps(turns, indent=2)
        cart_text = json.dumps(current_cart["cart_items"], indent=2)
        menu_text = json.dumps(MENU_INDEX, indent=2)
        rules_text = json.dumps(GLOBAL_RULES, indent=2)

        system_instruction = f"""You are System 2, the Background Brain for The Neon Trompo.
You receive a structured sequence of Conversation Turns (User and Agent roles) and the current Cart JSON. You make ALL logical decisions.

RULES FOR ASYNC SPEECH (SINGLE STRING OUTPUT):
1. REJECTIONS & AMBIGUITY: Handle off-menu or generic requests politely.
2. QUERIES: Answer questions using default_ingredients and description.
3. ORDER REVIEW (IMPLICIT CHECKOUT): If the user indicates they are done ordering (e.g., "that will be all"), DO NOT finalize the call immediately. Set `semantic_checkout` to `implicit`. Read back their ENTIRE current order. CRITICAL: DO NOT give the total price or say "Your total is..." during an implicit checkout. Explicitly ask for confirmation (e.g., "Is that all correct?").
4. ORDER FINALIZATION (EXPLICIT CHECKOUT - CRITICAL): Look at the exact last two turns. IF the Agent recently asked to confirm the order (e.g., "Does that sound correct?", "look right?", "Is that all correct?") AND the User's newest message is an affirmative response (e.g., "yes", "correct", "yep", "sure"):
   - You MUST set `semantic_checkout` to `explicit`.
   - You MUST NOT calculate the price yourself. You MUST include the exact literal string "[TOTAL]" in your async_speech (e.g., "Great! Your total is [TOTAL]. We'll have that right out for you.").
5. MOMENTUM: Always provide a momentum phrase unless explicitly checking out.
6. KITCHEN APPROVALS & WEAVING (CRITICAL):
   - Status "pending_hitl" = Still waiting. DO NOT bring this up unprompted. Only mention you are still waiting if the user explicitly asks.
   - Status "confirmed" (on an item with special_instructions) = KITCHEN APPROVED.
   - DENIALS: If the Turn History shows the Agent stated the kitchen CANNOT fulfill a modification, DO NOT re-add that modification and DO NOT hallucinate an approval. Accept the denial and move on.
   - Read the Turn History: If an item is 'confirmed' but the Agent hasn't verbally announced the approval yet, you MUST announce it now.
   - WEAVE YOUR SPEECH: If you need to announce an approval AND acknowledge a new item, weave them together smoothly.
7. STT STUMBLES: Do not double-count items already in the cart.

Menu Index Reference: {menu_text}
Global Rules: {rules_text}

You MUST output valid JSON only. You MUST include a "thought_process" field first to analyze the conversation state:
{{
    "thought_process": "Analyze the last 2 turns. Did the agent ask a confirmation question? Did the user answer affirmatively? If yes, explicit checkout.",
    "updated_cart": [ {{ "internal_uid": "str", "item_id": "str", "qty": 1, "tracked_modifiers": ["str"], "special_instructions": ["str"], "status": "confirmed" | "pending_hitl" }} ],
    "directives": {{
        "fumble_detected": false,
        "semantic_checkout": "none" | "implicit" | "explicit",
        "hitl_pending": false,
        "async_speech": "string"
    }}
}}"""

        prompt = f"Current Cart Items: {cart_text}\nConversation History: {history_text}\n\nAnalyze the history and cart. Return the JSON."
        self.log.debug("sys2_prompt_prepared", prompt_length=len(prompt))

        delays = [1, 2, 4, 8]
        for attempt in range(5):
            try:
                # SMART FALLBACK: If 'pro' is experiencing a 503 outage, fallback to 'flash' instantly
                current_model = "gemini-2.5-pro" if attempt < 2 else "gemini-2.5-flash"
                self.log.info("sys2_llm_request_started", attempt=attempt, model=current_model)

                start_time = time.time()
                response = await self.client.aio.models.generate_content(
                    model=current_model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.0,
                        response_mime_type="application/json",
                    ),
                )
                latency = time.time() - start_time
                self.log.info(
                    "sys2_llm_request_finished", latency=round(latency, 2), model=current_model
                )

                # Safely parse text in case Gemini wraps in markdown despite mime_type config
                raw_text = response.text.strip()
                self.log.debug("sys2_llm_raw_response", raw_text=raw_text)

                if raw_text.startswith("```"):
                    raw_text = raw_text.split("\n", 1)[-1].rsplit("\n", 1)[0].strip()

                data = json.loads(raw_text)

                # Print thought process to console for debugging
                if "thought_process" in data:
                    self.log.info("sys2_thought_process", thought_process=data["thought_process"])

                # Update cart manager state based on System 2's validation
                for item_dict in data.get("updated_cart", []):
                    try:
                        item = CartItem(**item_dict)
                        self.cart_manager.add_or_update_item(item)
                    except ValidationError as ve:
                        self.log.warning(
                            "sys2_cart_item_validation_error", error=str(ve), item_dict=item_dict
                        )
                    except Exception as e:
                        self.log.warning(
                            "sys2_cart_item_parse_error", error=str(e), item_dict=item_dict
                        )

                directives = data.get("directives", {})
                self.log.info("sys2_process_order_complete", directives=directives)
                return directives

            except Exception as e:
                self.log.error(
                    "sys2_llm_generation_error",
                    attempt=attempt,
                    model=current_model,
                    error_type=type(e).__name__,
                    error=str(e),
                )

                if attempt < 4:
                    await asyncio.sleep(delays[attempt])
                else:
                    self.log.error("sys2_max_retries_exhausted", fallback_triggered=True)
                    # CRITICAL: Prevent silent UI failure so US-05 flow doesn't break
                    return {
                        "async_speech": "I'm sorry, I'm having trouble connecting to the kitchen right now. Could you please confirm that one more time?"
                    }
        return {}
