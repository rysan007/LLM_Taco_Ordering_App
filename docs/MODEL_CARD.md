# Model Card
## Intended Use
The Neon Trompo Voice Agent is intended to be used by customers of the Neon Trompo Tex-Mex food truck to place food and drink orders via a web-based conversational voice interface. The system acts as a digital cashier, guiding the user through the menu, answering basic dietary questions based on a fixed database, tracking active cart state, and facilitating complex or off-menu kitchen requests via an asynchronous Human-in-the-Loop (HITL) approval process. It is designed for low-latency, high-accuracy ordering in a commercial hospitality context.
## Limitations
The system currently operates with the following known limitations:
- Static Inventory Awareness: The agent relies on a static MENU_INDEX defined in the codebase. It does not possess real-time inventory awareness (e.g., knowing if the truck is out of barbacoa) unless the kitchen staff explicitly denies a related request via the HITL tablet interface.
- Payment Processing: The system handles order accumulation and "semantic checkout" (calculating the total and verbally confirming the final order). However, it is not equipped to securely collect PCI-compliant payment information (like credit card numbers) over the voice channel.
- Language Support: While the underlying Gemini models and Retell AI STT are resilient to code-mixing (Spanglish) and basic Spanish, the primary prompt scaffolding and menu descriptions are optimized for English. Highly rapid or complex non-English speech may result in degraded intent classification.
## Risks
- Hallucination (Fabricated Orders & Prices): LLMs frequently attempt to "help" by inventing items or altering prices to appease users. We mitigate this via a strict Semantic ID architecture. The LLM never calculates the total or adds plain text to the cart; it can only output exact IDs (e.g., taco_pastor). The deterministic Python CartManager calculates all prices, making price hallucination impossible.
- Prompt Injection: Adversarial users might attempt to inject commands (e.g., "Apply a 100% discount" or "Ignore previous instructions"). This is mitigated by our data models: System 2's JSON output schema does not permit price modification fields, and the backend ignores any Semantic IDs not found in the hardcoded MENU_INDEX.
- Bias and Speech Recognition: Speech-to-Text engines often struggle with regional accents or Tex-Mex slang (e.g., mishearing "barbacoa"). We mitigate this using System 1's "Active Echoing" protocol, which is explicitly prompted to correct misspellings gracefully, ensuring users from diverse linguistic backgrounds feel understood.
- Privacy: User voice interactions are transcribed and stored as text logs in logs/conversations/ to facilitate context tracking and system debugging. To mitigate privacy risks, the system is explicitly designed not to request Personally Identifiable Information (PII) during the ordering phase.
- Cost Management: Malicious conversational loops or extended silences could drain API credits. This is mitigated by Retell AI's automatic endpointing/call timeouts, and our Multi-LLM architecture. By delegating high-frequency stall phrases to the ultra-cheap gemini-2.5-flash model (System 1), we reserve the more expensive gemini-2.5-pro model (System 2) only for heavy cart mutations.
## Out of Scope
The agent is strictly a food ordering conduit. It is explicitly programmed to politely refuse and redirect requests involving:
- General AI conversational assistance (e.g., "tell me a joke", "write a poem").
- Providing medical guarantees or severe allergy assurances beyond the pre-approved dietary tags in the menu index.
- Processing live credit card numbers or executing financial transactions.
- Handling customer service complaints, refunds, or directions to the food truck.
- Executing arbitrary code or processing multimedia uploads.
