import json

from google import genai
from google.genai import types

from src.myproject.menu import MENU_INDEX
from src.myproject.models import CartState


class ForegroundAgent:
    def __init__(self, api_key: str, cart_manager=None) -> None:
        self.api_key = api_key
        self.client = genai.Client(api_key=self.api_key) if api_key != "dummy_key" else None
        self._cache = {}
        self.cart_manager = cart_manager

    async def process_intake(self, transcript: str) -> dict:
        if not self.client:
            return {"intent_type": "unknown", "response_text": "Please configure GEMINI_API_KEY."}

        state = self.cart_manager.get_state() if self.cart_manager else None
        cart_memory = "Cart is currently empty."
        if state and state.cart_items:
            item_strings = []
            for item in state.cart_items:
                name = MENU_INDEX.get(item.item_id, {}).get("name", item.item_id)
                item_strings.append(f"{item.qty}x {name}")
            cart_memory = ", ".join(item_strings)

        cache_key = transcript.strip().lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        system_instruction = f"""You are System 1 (Foreground Staller) for The Neon Trompo voice agent.
Your ONLY job is to acknowledge the user immediately to prevent dead air. YOU HAVE NO DECISION-MAKING POWER.

CURRENT CART MEMORY: {cart_memory}

RULES:
1. IF ORDER (NEUTRAL ECHO): You MUST blindly and NEUTRALLY mirror exactly what they ordered back to them (e.g., "One cheeseburger, adding that now" or "One pastor taco..."). HOWEVER, if the user's speech contains obvious Speech-to-Text misspellings of Tex-Mex items (e.g., 'Arbacola' -> 'barbacoa'), politely echo the CORRECTED word so they know they were understood. NEVER use isolated affirming words like "Got it", "Okay", or "Sure". DO NOT verify if it's on the menu.
2. IF QUERY: Stall (e.g., "Let me check the menu for you real quick...")
3. IF CHECKOUT (e.g., "That's everything"): Stall (e.g., "Sure, let me gather your order for review and calculate your total...")
4. MODIFIERS/QUANTITY: If they say "make that two" or "actually no onions", use CART MEMORY to figure out what they mean and neutrally mirror it back (e.g., "Updating to two, one moment...").
5. PRONOUNS & AGREEMENT (e.g., "I'll take one of those", "Yep", "Yes", "Sure", "Looks good"): You do not know what they are agreeing to. Provide a brief, neutral acknowledgment (e.g., "Noted, processing...", "Alright, one moment..."). DO NOT assume they are checking out, and DO NOT say you are checking the menu.

You MUST output valid JSON only, matching this schema:
{{
  "intent_type": "order" | "generic_query" | "fumbled_speech" | "checkout",
  "response_text": "Your fast stall or mirroring phrase."
}}"""

        try:
            response = await self.client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"User said: {transcript}",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    temperature=0.0,
                ),
            )
            intent_dict = json.loads(response.text)
            self._cache[cache_key] = intent_dict
            return intent_dict

        except Exception as e:
            print(f"\n\n!!! GEMINI ERROR (Intake): {e} !!!\n\n")
            return {
                "intent_type": "fumbled_speech",
                "response_text": "Sorry, I missed that. Could you repeat?",
            }

    async def generate_response(self, state: CartState, hitl_updates: list) -> str:
        return f"Your total is currently ${state.running_total:.2f}. What else?"
